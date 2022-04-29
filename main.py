import streamlit as st 
import pandas as pd
import numpy as np
import altair as alt
import os
import time
from datetime import datetime
import pickle
import itertools
import scipy.optimize as sco
import plotly.express as px
from plt_setup import finastra_theme
from download_data import Data
from Markowitz_Portfolio import *
import sys

import metadata_parser

####### CACHED FUNCTIONS ######
@st.cache(show_spinner=False, suppress_st_warning=True)
def filter_company_data(df_company, esg_categories, start, end):
    #Filter E,S,G Categories
    comps = []
    for i in esg_categories:
        X = df_company[df_company[i] == True]
        comps.append(X)
    df_company = pd.concat(comps)
    # df_company = df_company[(df_company.DATE >= start) &
    #                         (df_company.DATE <= end)]
    df_company = df_company[df_company.DATE.between(start, end)]
    return df_company


@st.cache(show_spinner=False, suppress_st_warning=True,
          allow_output_mutation=True)
def load_data(start_data, end_data, flag):
    data = Data().read(start_data, end_data, flag)
    companies = data["data"].Organization.sort_values().unique().tolist()
    if flag == 'USA':
        companies.remove('netflix')
        companies.insert(0,"netflix")
    elif flag == 'UK':
        companies.remove('astrazeneca')
        companies.insert(0,"astrazeneca")
    elif flag == 'CANADA':
        companies.remove('enbridge')
        companies.insert(0, 'enbridge')
    #elif flag == 'AUSTRALIA':
    #    companies.remove('national australia bank ltd')
    #    companies.insert(0, 'national australia bank ltd')
    return data, companies


@st.cache(show_spinner=False,suppress_st_warning=True)
def filter_publisher(df_company,publisher):
    if publisher != 'all':
        df_company = df_company[df_company['SourceCommonName'] == publisher]
    return df_company


def get_melted_frame(data_dict, frame_names, keepcol=None, dropcol=None):
    if keepcol:
        reduced = {k: df[keepcol].rename(k) for k, df in data_dict.items()
                   if k in frame_names}
    else:
        reduced = {k: df.drop(columns=dropcol).mean(axis=1).rename(k)
                   for k, df in data_dict.items() if k in frame_names}
    df = (pd.concat(list(reduced.values()), axis=1).reset_index().melt("date")
            .sort_values("date").ffill())
    df.columns = ["DATE", "ESG", "Score"]
    return df.reset_index(drop=True)


def filter_on_date(df, start, end, date_col="DATE"):
    df = df[(df[date_col] >= pd.to_datetime(start)) &
            (df[date_col] <= pd.to_datetime(end))]
    return df


def get_clickable_name(url):
    try:
        T = metadata_parser.MetadataParser(url=url, search_head_only=True)
        title = T.metadata["og"]["title"].replace("|", " - ")
        return f"[{title}]({url})"
    except:
        try:
            title = []
            for i in range(len(list(url))-1,0,-1):
                if list(url)[i] == '/' and len(title)!=0:
                    break
                else:
                    if list(url)[i] == '/':
                        pass
                    else:
                        title.append(list(url)[i])
                    
            title = ''.join(reversed(title))
            return f"[{title}]({url})"
        except:
            return f"[{url}]({url})"



def main(start_data, end_data):
    ###### CUSTOMIZE COLOR THEME ######
    alt.themes.register("finastra", finastra_theme)
    alt.themes.enable("finastra")
    violet, fuchsia = ["#694ED6", "#C137A2"]


    ###### SET UP PAGE ######
    icon_path = os.path.join("./img", "KBlogo.jpg")
    st.set_page_config(page_title="ESG AI", page_icon=icon_path,
                       layout='centered', initial_sidebar_state="collapsed")
    _, logo, _ = st.columns(3)
    logo.image(icon_path, width=230)
    style = ("text-align:center; padding: 0px; font-family: arial black;, "
             "font-size: 400%")
    title = f"<h1 style='{style}'>ESG<sup>AI</sup></h1><br><br>"
    st.write(title, unsafe_allow_html=True)
    
    
    ####### CREATE SIDEBAR CATEGORY FILTER######
    st.sidebar.title("세부 옵션을 선택하세요")
    date_place = st.sidebar.empty()
    esg_categories = st.sidebar.multiselect("기사 테마 중 ESG 옵션을 선택하세요",
                                            ["E", "S", "G"], ["E", "S", "G"])
    pub = st.sidebar.empty()
    num_neighbors = st.sidebar.slider("포트폴리오구성을 위한 유사 기업 수를 선택하세요", 1, 20, value=8)


    ###### LayOut ######           
    box1, box2 = st.columns([1, 1.5])    
    
    ###### LOAD DATA ######  
    ###default setting### 
    market = 'USA'
    INFO = '기업을 선택하세요'
    state = []
    with box1:
        st.write('<style>div.row-widget.stRadio > div{flex-direction:row;}</style>', unsafe_allow_html=True)
        market_options = ["USA", "UK", "CANADA"]
        market_metric = st.radio("나라를 선택하세요", options=market_options)
    with box2:
        with st.spinner(text="데이터를 로딩중입니다..."):
            data, companies = load_data(start_data, end_data, market_metric)

            df_conn = data["conn"]
            df_data = data["data"]
            embeddings = data["embed"]  

        company = st.selectbox(INFO, companies)         
    
        
    ###### FILTER ######
    df_company = df_data[df_data.Organization == company]
    diff_col = f"{company.replace(' ', '_')}_diff"
    tone_df = get_melted_frame(data, ["overall_score"], keepcol=diff_col)
    ind_tone_df = get_melted_frame(data, ["overall_score"],
                                   dropcol="industry_tone")
    
    esg_keys = ["E_score", "S_score", "G_score"]
    e_df = get_melted_frame(data, esg_keys[0], keepcol=diff_col)
    ind_e_df = get_melted_frame(data, esg_keys[0], dropcol="industry_tone")
    s_df = get_melted_frame(data, esg_keys[1], keepcol=diff_col)
    ind_s_df = get_melted_frame(data, esg_keys[1], dropcol="industry_tone")
    g_df = get_melted_frame(data, esg_keys[2], keepcol=diff_col)
    ind_g_df = get_melted_frame(data, esg_keys[2], dropcol="industry_tone")


    ###### DATE WIDGET ######
    start = df_company.DATE.min()
    end = df_company.DATE.max()
    selected_dates = date_place.date_input("날짜를 선택하세요",
        value=[start, end], min_value=start, max_value=end, key=None)
    time.sleep(0.8)  #Allow user some time to select the two dates -- hacky :D
    start, end = selected_dates


    ###### FILTER DATA ######
    df_company = filter_company_data(df_company, esg_categories,
                                     start, end)
    df_company = df_company.drop_duplicates(keep='last', subset=['DATE', 'SourceCommonName'])
    tone_df = filter_on_date(tone_df, start, end)
    ind_tone_df = filter_on_date(ind_tone_df, start, end)
    date_filtered = filter_on_date(df_data, start, end)
    
    e_df = filter_on_date(e_df, start, end)
    ind_e_df = filter_on_date(ind_e_df, start, end)
    s_df = filter_on_date(s_df, start, end)
    ind_s_df = filter_on_date(ind_s_df, start, end)
    g_df = filter_on_date(g_df, start, end)
    ind_g_df = filter_on_date(ind_g_df, start, end)


    ###### PUBLISHER SELECT BOX ######
    publishers = df_company.SourceCommonName.sort_values().unique().tolist()
    publishers.insert(0, "all")
    publisher = pub.selectbox("언론사를 선택하세요", publishers)
    df_company = filter_publisher(df_company, publisher)


    ###### DISPLAY DATA ######
    URL_Expander = st.expander(f"{company.title()}의 ESG 테마 기사: ", True)
    URL_Expander.write(f"### 선택된 {company.title()}의 {len(df_company):,d}개 ESG 테마 기사의 어조 분석 표입니다")
    display_cols = ["DATE", "SourceCommonName", "Tone", "Polarity",
                    "NegativeTone", "PositiveTone"]  #  "WordCount"
    URL_Expander.write(df_company[display_cols][::-1])

    
    ####
    URL_Expander.write(f"#### 최근 5일의 샘플 기사입니다")
    link_df = df_company[["DATE", "URL"]].drop_duplicates(keep='last', subset='DATE').tail(5).copy()
    # link_df["URL"] = link_df["URL"].apply(lambda R: f"[{R}]({R})")
    link_df["ARTICLE"] = link_df.URL.apply(get_clickable_name)
    link_df = link_df[["DATE", "ARTICLE"]][::-1].to_markdown(index=False)
    URL_Expander.markdown(link_df)
    ####   


    ###### CHART: METRIC OVER TIME ######
    st.markdown("---")
        
    ###### NUMBER OF NEIGHBORS TO FIND #####
    neighbor_cols = [f"n{i}_rec" for i in range(num_neighbors)]
    company_df = df_conn[df_conn.company == company]
    try:
        neighbors = company_df[neighbor_cols].iloc[0]
    except:
        neighbors = []
        print("유사 기업이 없습니다")
  
    col1, col2 = st.columns((1.2, 4))
    metric_options = ["Tone", "NegativeTone", "PositiveTone", "Polarity",
                      "WordCount", "E Score", "S Score", "G Score"]
    metric_options = ["어조", "부정적 어조", "긍정적 어조", "양극성", "단어수", "E 점수", "S 점수", "G 점수"]
    line_metric = col1.radio("평가 지표를 선택하세요", options=metric_options)

    if line_metric == "E 점수":
        # Get E Scores
        e_df["WHO"] = company.title()
        ind_e_df["WHO"] = "Industry Average"
        esg_plot_df = pd.concat([e_df, ind_e_df]
                                ).reset_index(drop=True)
  
        esg_plot_df.replace({"E_score": "Environment"}, inplace=True)

        metric_chart = alt.Chart(esg_plot_df, title=f"{line_metric} 시계열 그래프", padding={"left": 30, "top": 1, "right": 10, "bottom": 1}
                                   ).mark_line().encode(
            x=alt.X("yearmonthdate(DATE):O", title=""), #title="DATE"
            y=alt.Y("Score:Q", title="E Score"),
            color=alt.Color("WHO", sort=None, legend=alt.Legend(
                title=None, orient="top")),
            strokeDash=alt.StrokeDash("WHO", sort=None, legend=alt.Legend(
                title=None, symbolType="stroke", symbolFillColor="gray",
                symbolStrokeWidth=4, orient="top")),
            tooltip=["DATE", alt.Tooltip("Score", format=".5f")]
            )
    elif line_metric == "S 점수":
        # Get E Scores
        s_df["WHO"] = company.title()
        ind_s_df["WHO"] = "Industry Average"
        esg_plot_df = pd.concat([s_df, ind_s_df]
                                ).reset_index(drop=True)
        
        esg_plot_df.replace({"S_score": "Social"}, inplace=True)

        metric_chart = alt.Chart(esg_plot_df, title=f"{line_metric} 시계열 그래프", padding={"left": 30, "top": 1, "right": 10, "bottom": 1}
                                   ).mark_line().encode(
            x=alt.X("yearmonthdate(DATE):O", title=""), #title="DATE"
            y=alt.Y("Score:Q", title="S Score"),
            color=alt.Color("WHO", sort=None, legend=alt.Legend(
                title=None, orient="top")),
            strokeDash=alt.StrokeDash("WHO", sort=None, legend=alt.Legend(
                title=None, symbolType="stroke", symbolFillColor="gray",
                symbolStrokeWidth=4, orient="top")),
            tooltip=["DATE", alt.Tooltip("Score", format=".5f")]
            )
    elif line_metric == "G 점수":
        # Get E Scores
        g_df["WHO"] = company.title()
        ind_g_df["WHO"] = "Industry Average"
        esg_plot_df = pd.concat([g_df, ind_g_df]
                                ).reset_index(drop=True)
        
        esg_plot_df.replace({"G_score": "Governance"}, inplace=True)

        metric_chart = alt.Chart(esg_plot_df, title=f"{line_metric} 시계열 그래프", padding={"left": 30, "top": 1, "right": 10, "bottom": 1}
                                   ).mark_line().encode(
            x=alt.X("yearmonthdate(DATE):O", title=""), #title="DATE"
            y=alt.Y("Score:Q", title="G Score"),
            color=alt.Color("WHO", sort=None, legend=alt.Legend(
                title=None, orient="top")),
            strokeDash=alt.StrokeDash("WHO", sort=None, legend=alt.Legend(
                title=None, symbolType="stroke", symbolFillColor="gray",
                symbolStrokeWidth=4, orient="top")),
            tooltip=["DATE", alt.Tooltip("Score", format=".5f")]
            )
    else:
        if line_metric == '어조':
            line_metric_ = "Tone"
        elif line_metric == '부정적 어조':
            line_metric_ = "NegativeTone"
        elif line_metric == '긍정적 어조':
            line_metric_ = "PositiveTone"
        elif line_metric == '양극성':
            line_metric_ = "Polarity"
        elif line_metric == '단어수':
            line_metric_ = "WordCount"
        elif line_metric == 'E 점수':
            line_metric_ = "E Score"
        elif line_metric == 'S 점수':
            line_metric_ = "S Score"
        elif line_metric == 'G 점수':
            line_metric_ = "G Score"
        
        df1 = df_company.groupby("DATE")[line_metric_].mean(
            ).reset_index()
        df2 = filter_on_date(df_data.groupby("DATE")[line_metric_].mean(
            ).reset_index(), start, end)
        df1["WHO"] = company.title()
        df2["WHO"] = "Industry Average"
        plot_df = pd.concat([df1, df2]).reset_index(drop=True)
        metric_chart = alt.Chart(plot_df, title=f"{line_metric} 시계열 그래프", padding={"left": 40, "top": 1, "right": 10, "bottom": 1}
                             ).mark_line().encode(
        x=alt.X("yearmonthdate(DATE):O", title=""),
        y=alt.Y(f"{line_metric_}:Q", scale=alt.Scale(type="linear")),
        color=alt.Color("WHO", legend=None),
        strokeDash=alt.StrokeDash("WHO", sort=None,
            legend=alt.Legend(
                title=None, symbolType="stroke", symbolFillColor="gray",
                symbolStrokeWidth=4, orient="top",
                ),
            ),
        tooltip=["DATE", alt.Tooltip(line_metric_, format=".3f")]
        )
    metric_chart = metric_chart.properties(
        height=340,
        width=200
    ).interactive()
    col2.altair_chart(metric_chart, use_container_width=True)
    
    empty, box = st.columns((1.3, 4))
    with empty:
        pass
    with box:
        with st.expander("펼쳐보기"):
            for i in range(1, len(metric_options)-3):
                df1 = df_company.groupby("DATE")[metric_options[i]].mean(
                ).reset_index()
                df2 = filter_on_date(df_data.groupby("DATE")[metric_options[i]].mean(
                    ).reset_index(), start, end)
                df1["WHO"] = company.title()
                df2["WHO"] = "Industry Average"
                plot_df = pd.concat([df1, df2]).reset_index(drop=True)
                metric_chart = alt.Chart(plot_df, title=f"{metric_options[i]} 시계열 그래프", padding={"left": 40, "top": 1, "right": 10, "bottom": 1}
                                         ).mark_line().encode(
                    x=alt.X("yearmonthdate(DATE):O", title=""),
                    y=alt.Y(f"{metric_options[i]}:Q", scale=alt.Scale(type="linear")),
                    color=alt.Color("WHO", legend=None),
                    strokeDash=alt.StrokeDash("WHO", sort=None,
                        legend=alt.Legend(
                            title=None, symbolType="stroke", symbolFillColor="gray",
                            symbolStrokeWidth=4, orient="top",
                            ),
                        ),
                    tooltip=["DATE", alt.Tooltip(metric_options[i], format=".3f")]
                    )
                metric_chart = metric_chart.properties(
                    height=340,
                    width=200
                ).interactive()
                st.altair_chart(metric_chart, use_container_width=True)
            for i in range(3):
                if i == 0:
                    e_df["WHO"] = company.title()
                    ind_e_df["WHO"] = "Industry Average"
                    esg_plot_df = pd.concat([e_df, ind_e_df]
                                            ).reset_index(drop=True)
                    esg_plot_df.replace({"E_score": "Environment"}, inplace=True)
                elif i==1:
                    s_df["WHO"] = company.title()
                    ind_s_df["WHO"] = "Industry Average"
                    esg_plot_df = pd.concat([s_df, ind_s_df]
                                            ).reset_index(drop=True)
                    esg_plot_df.replace({"S_score": "Social"}, inplace=True)
                else:
                    g_df["WHO"] = company.title()
                    ind_g_df["WHO"] = "Industry Average"
                    esg_plot_df = pd.concat([g_df, ind_g_df]
                                            ).reset_index(drop=True)

                    esg_plot_df.replace({"G_score": "Governance"}, inplace=True)

                metric_chart = alt.Chart(esg_plot_df, title=f"{metric_options[len(metric_options)-3+i]} 시계열 그래프", padding={"left": 30, "top": 1, "right": 10, "bottom": 1}
                                           ).mark_line().encode(
                    x=alt.X("yearmonthdate(DATE):O", title=""), #title="DATE"
                    y=alt.Y("Score:Q", title=metric_options[len(metric_options)-3+i]),
                    color=alt.Color("WHO", sort=None, legend=alt.Legend(
                        title=None, orient="top")),
                    strokeDash=alt.StrokeDash("WHO", sort=None, legend=alt.Legend(
                        title=None, symbolType="stroke", symbolFillColor="gray",
                        symbolStrokeWidth=4, orient="top")),
                    tooltip=["DATE", alt.Tooltip("Score", format=".5f")]
                    )
                metric_chart = metric_chart.properties(
                    height=340,
                    width=200
                ).interactive()
                st.altair_chart(metric_chart, use_container_width=True)

    st.markdown("---")
    st.write('<style>div.row-widget.stRadio > div{flex-direction:row;}</style>', unsafe_allow_html=True)
    choose_graph = ["ESG Rader", "Tone Density", "Polarity Graph", "Company Distribution", "Similarity Company & Score"]
    if len(neighbors)==0:
        choose_graph = ["ESG Rader", "Tone Density", "Polarity Graph"]
    graph_metric = st.radio("차트를 선택하세요", options=choose_graph)
    
    ###### CHART: ESG RADAR ######
    if graph_metric == 'ESG Rader':
        avg_esg = data["ESG"]
        avg_esg.rename(columns={"Unnamed: 0": "Type"}, inplace=True)
        avg_esg.replace({"T": "Overall", "E": "Environment",
                         "S": "Social", "G": "Governance"}, inplace=True)
        avg_esg["Industry Average"] = avg_esg.mean(axis=1)

        radar_df = avg_esg[["Type", company, "Industry Average"]].melt("Type",
            value_name="score", var_name="entity")

        radar = px.line_polar(radar_df, r="score", theta="Type",
            color="entity", line_close=True, hover_name="Type",
            hover_data={"Type": True, "entity": True, "score": ":.2f"},
            color_discrete_map={"Industry Average": fuchsia, company: violet})
        radar.update_layout(template=None,
                            polar={
                                   "radialaxis": {"showticklabels": False,
                                                  "ticks": ""},
                                   "angularaxis": {"showticklabels": False,
                                                   "ticks": ""},
                                   },
                            legend={"title": None, "yanchor": "middle",
                                    "orientation": "h"},
                            title={"text": "<b>ESG 레이터 차트</b>",
                                   "x": 0.15, "y": 0.93,
                                   "xanchor": "center",
                                   "yanchor": "top",
                                   "font": {"family": "Futura", "size": 23}},
                            margin={"l": 5, "r": 5, "t": 0, "b": 0},
                            )#0.8875
        radar.update_layout(showlegend=False)
        st.plotly_chart(radar, use_container_width=True)

    elif graph_metric == 'Tone Density':
        ###### CHART: DOCUMENT TONE DISTRIBUTION #####
        # add overall average
        dist_chart = alt.Chart(df_company, title="선택한 ESG 경영 기업의 기사 밀도 차트", padding={"left": 1, "top": 10, "right": 25, "bottom": 1}
                               ).transform_density(
                density='Tone',
                as_=["Tone", "density"]
            ).mark_area(opacity=0.5,color="purple").encode(
                    x=alt.X('Tone:Q', scale=alt.Scale(domain=(-10, 10)), title="Tone"),
                    y=alt.Y('density:Q', title="Density"),
                    tooltip=[alt.Tooltip("Tone", format=".3f"),
                             alt.Tooltip("density:Q", format=".4f")]
                ).properties(
                    height=325,
                ).configure_title(
                    dy=-10
                ).interactive()
        st.markdown("### <br>", unsafe_allow_html=True)
        st.altair_chart(dist_chart,use_container_width=True)


    ###### CHART: SCATTER OF ARTICLES OVER TIME #####
    elif graph_metric == 'Polarity Graph':
        scatter = alt.Chart(df_company, title= "단어 양극성 차트", padding={"left": 10, "top": 10, "right": 1, "bottom": 1}).mark_circle().encode(
            x=alt.X("NegativeTone:Q", title="Negative Tone"),
            y=alt.Y("PositiveTone:Q", title="Positive Tone"),
            size="WordCount:Q",
            color=alt.Color("Polarity:Q", scale=alt.Scale()),
            tooltip=[alt.Tooltip("Polarity", format=".3f"),
                     alt.Tooltip("NegativeTone", format=".3f"),
                     alt.Tooltip("PositiveTone", format=".3f"),
                     alt.Tooltip("DATE"),
                     alt.Tooltip("WordCount", format=",d"),
                     alt.Tooltip("SourceCommonName", title="Site")]
            ).properties(
                height=440
            ).interactive()
        st.altair_chart(scatter, use_container_width=True)

        
    ###### CHART: 3D EMBEDDING WITH NEIGHBORS ######
    elif graph_metric == 'Company Distribution' and len(neighbors)!=0:
        color_f = lambda f: f"Company: {company.title()}" if f == company else (
            "Connected Company" if f in neighbors.values else "Other Company")
        embeddings["colorCode"] = embeddings.company.apply(color_f)
        point_colors = {company: violet, "Connected Company": fuchsia,
                        "Other Company": "lightgrey"}
        fig_3d = px.scatter_3d(embeddings, x="0", y="1", z="2",
                               color='colorCode',
                               color_discrete_map=point_colors,
                               opacity=0.4,
                               hover_name="company",
                               hover_data={c: False for c in embeddings.columns},
                               )
        fig_3d.update_layout(legend={"orientation": "h",
                                     "yanchor": "bottom",
                                     "title": None},
                             title={"text": "<b>유사 기업 분포 차트</b>",
                                    "x": 0.5, "y": 0.9,
                                    "xanchor": "center",
                                    "yanchor": "top",
                                    "font": {"family": "Futura", "size": 23}},
                             scene={"xaxis": {"visible": False},
                                    "yaxis": {"visible": False},
                                    "zaxis": {"visible": False}},
                             margin={"l": 0, "r": 0, "t": 0, "b": 0},
                             )
        st.plotly_chart(fig_3d, use_container_width=True)


    ###### CHART: NEIGHBOR SIMILIARITY ######
    elif graph_metric == 'Similarity Company & Score' and len(neighbors)!=0:
        neighbor_conf = pd.DataFrame({
            "Neighbor": neighbors,
            "Confidence": company_df[[f"n{i}_conf" for i in
                                      range(num_neighbors)]].values[0]})
        conf_plot = alt.Chart(neighbor_conf, title=f"상위 {num_neighbors}개 유사 기업의 유사도 점수 차트", padding={"left": 1, "top": 10, "right": 1, "bottom": 1}
                              ).mark_bar().encode(
            x=alt.X("Confidence:Q", title="유사 정도"),
            y=alt.Y("Neighbor:N", sort="-x", title="유사 "),
            tooltip=["Neighbor", alt.Tooltip("Confidence", format=".3f")],
            color=alt.Color("Confidence:Q", scale=alt.Scale(), legend=None)
        ).properties(
            height=25 * num_neighbors + 90
        ).configure_axis(grid=False)
        st.altair_chart(conf_plot, use_container_width=True)
                
        
    with st.expander("펼쳐보기"):
        ###### CHART: DOCUMENT TONE DISTRIBUTION #####
        # add overall average
        dist_chart = alt.Chart(df_company, title="선택한 ESG 경영 기업의 기사 밀도 차트 ", padding={"left": 1, "top": 10, "right": 25, "bottom": 1}
                               ).transform_density(
                density='Tone',
                as_=["Tone", "density"]
            ).mark_area(opacity=0.5,color="purple").encode(
                    x=alt.X('Tone:Q', scale=alt.Scale(domain=(-10, 10)), title="Tone"),
                    y=alt.Y('density:Q', title="Density"),
                    tooltip=[alt.Tooltip("Tone", format=".3f"),
                             alt.Tooltip("density:Q", format=".4f")]
                ).properties(
                    height=325,
                ).configure_title(
                    dy=-10
                ).interactive()
        st.markdown("### <br>", unsafe_allow_html=True)
        st.altair_chart(dist_chart,use_container_width=True)
        
        scatter = alt.Chart(df_company, title= "단어 양극성 차트", padding={"left": 10, "top": 10, "right": 1, "bottom": 1}).mark_circle().encode(
            x=alt.X("NegativeTone:Q", title="Negative Tone"),
            y=alt.Y("PositiveTone:Q", title="Positive Tone"),
            size="WordCount:Q",
            color=alt.Color("Polarity:Q", scale=alt.Scale()),
            tooltip=[alt.Tooltip("Polarity", format=".3f"),
                     alt.Tooltip("NegativeTone", format=".3f"),
                     alt.Tooltip("PositiveTone", format=".3f"),
                     alt.Tooltip("DATE"),
                     alt.Tooltip("WordCount", format=",d"),
                     alt.Tooltip("SourceCommonName", title="Site")]
            ).properties(
                height=440
            ).interactive()
        st.altair_chart(scatter, use_container_width=True)
        
        if len(neighbors)!=0:
            color_f = lambda f: f"Company: {company.title()}" if f == company else (
                "Connected Company" if f in neighbors.values else "Other Company")
            embeddings["colorCode"] = embeddings.company.apply(color_f)
            point_colors = {company: violet, "Connected Company": fuchsia,
                            "Other Company": "lightgrey"}
            fig_3d = px.scatter_3d(embeddings, x="0", y="1", z="2",
                                   color='colorCode',
                                   color_discrete_map=point_colors,
                                   opacity=0.4,
                                   hover_name="company",
                                   hover_data={c: False for c in embeddings.columns},
                                   )
            fig_3d.update_layout(legend={"orientation": "h",
                                         "yanchor": "bottom",
                                         "title": None},
                                 title={"text": "<b>유사 기업 분포 차트</b>",
                                        "x": 0.5, "y": 0.9,
                                        "xanchor": "center",
                                        "yanchor": "top",
                                        "font": {"family": "Futura", "size": 23}},
                                 scene={"xaxis": {"visible": False},
                                        "yaxis": {"visible": False},
                                        "zaxis": {"visible": False}},
                                 margin={"l": 0, "r": 0, "t": 0, "b": 0},
                                 )
            st.plotly_chart(fig_3d, use_container_width=True)
            
            neighbor_conf = pd.DataFrame({
            "Neighbor": neighbors,
            "Confidence": company_df[[f"n{i}_conf" for i in
                                      range(num_neighbors)]].values[0]})
            conf_plot = alt.Chart(neighbor_conf, title=f"상위 {num_neighbors}개 유사 기업의 유사도 점수 차트", padding={"left": 1, "top": 10, "right": 1, "bottom": 1}
                                  ).mark_bar().encode(
                x=alt.X("Confidence:Q", title="유사 정도"),
                y=alt.Y("Neighbor:N", sort="-x", title="유사 "),
                tooltip=["Neighbor", alt.Tooltip("Confidence", format=".3f")],
                color=alt.Color("Confidence:Q", scale=alt.Scale(), legend=None)
            ).properties(
                height=25 * num_neighbors + 90
            ).configure_axis(grid=False)
            st.altair_chart(conf_plot, use_container_width=True)
            
    if market_metric == 'USA':
        st.markdown("---")
        portfolio1 = data["Portfolio"][company]
        portfolio2 = data["Portfolio"][neighbors]
        table = pd.concat([portfolio1, portfolio2], axis=1)

        returns = table.pct_change()
        mean_returns = returns.mean()
        cov_matrix = returns.cov()
        num_portfolios = 25000
        risk_free_rate = 0.0178

        max_sharpe = max_sharpe_ratio(mean_returns, cov_matrix, risk_free_rate)
        sdp, rp = portfolio_annualised_performance(max_sharpe['x'], mean_returns, cov_matrix)
        max_sharpe_allocation = pd.DataFrame(max_sharpe.x,index=table.columns,columns=['allocation'])
        max_sharpe_allocation.allocation = [round(i*100,2)for i in max_sharpe_allocation.allocation]
        max_sharpe_allocation = pd.DataFrame({"company": max_sharpe_allocation.T.columns, "allocation": max_sharpe_allocation.T.loc['allocation']})

        min_vol = min_variance(mean_returns, cov_matrix)
        sdp_min, rp_min = portfolio_annualised_performance(min_vol['x'], mean_returns, cov_matrix)
        min_vol_allocation = pd.DataFrame(min_vol.x,index=table.columns,columns=['allocation'])
        min_vol_allocation.allocation = [round(i*100,2)for i in min_vol_allocation.allocation]
        min_vol_allocation = pd.DataFrame({"company": min_vol_allocation.T.columns, "allocation": min_vol_allocation.T.loc['allocation']})

        an_vol = np.std(returns) * np.sqrt(252)
        an_rt = mean_returns * 252

        choose_portfolio = ["Min Vol", "Max Sharpe"]
        portfolio_metric = st.radio("포트폴리오를 선택하세요", options=choose_portfolio)

        if portfolio_metric == 'Max Sharpe':
            pie_chart = alt.Chart(max_sharpe_allocation, title="높은 수익률의 포트폴리오 예시입니다").mark_arc().encode(
                        theta=alt.Theta(field="allocation", type="quantitative"),
                        color=alt.Color(field="company", type="nominal"),
                        ).properties(height=350)
            st.altair_chart(pie_chart, use_container_width=True) 
            st.write("연 평균 예상 수익:", round(rp,2))
            st.write("연 평균 포트폴리오 변동성:", round(sdp,2))
        else:
            pie_chart = alt.Chart(min_vol_allocation, title="변동성이 낮은 포트폴리오 예시입니다").mark_arc().encode(
                        theta=alt.Theta(field="allocation", type="quantitative"),
                        color=alt.Color(field="company", type="nominal"),
                        ).properties(height=350)
            st.altair_chart(pie_chart, use_container_width=True) 
            st.write("연 평균 예상 수익:", round(rp_min,2))
            st.write("연 평균 포트폴리오 변동성:", round(sdp_min,2))

        with st.expander("Spread Out"):
            pie_chart = alt.Chart(max_sharpe_allocation, title="높은 수익률의 포트폴리오 예시입니다").mark_arc().encode(
                        theta=alt.Theta(field="allocation", type="quantitative"),
                        color=alt.Color(field="company", type="nominal"),
                        ).properties(height=350)
            st.altair_chart(pie_chart, use_container_width=True) 
            st.write("연 평균 예상 수익:", round(rp,2))
            st.write("연 평균 포트폴리오 변동성:", round(sdp,2))
        

if __name__ == "__main__":
    args = sys.argv
    if len(args) != 3:
        start_data = "2022-01-01"
        end_data = "2022-04-26"
    else:
        start_data = args[1]
        end_data = args[2]
    print(start_data, end_data)
    if f"{start_data}__to__{end_data}" not in os.listdir("./Data"):
        print(f"There isn't data for {os.listdir('./Data')}")
        raise NameError(f"Please pick from {os.listdir('./Data')}")
        sys.exit()
        st.stop()
    else:
        print("streamlit start!")
        main(start_data, end_data)
    alt.themes.enable("default")
