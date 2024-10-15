#!/usr/bin/env python3
from nicegui import app, ui
import frost_sta_client as fsc
import pyecharts.options as opts
from pyecharts.charts import Line, Grid
import pandas as pd
import arrow

#x_data = []
#y_data_flow_amount = []
# Line().add_xaxis(xaxis_data=x_data).add_yaxis(
#     series_name="Some",
#     y_axis=y_data_flow_amount,
#     areastyle_opts=opts.AreaStyleOpts(opacity=0.5),
#     linestyle_opts=opts.LineStyleOpts(),
#     label_opts=opts.LabelOpts(is_show=False),
# ).add_yaxis(
#     series_name="Tair",
#     y_axis=y_data_rain_fall_amount,
#     yaxis_index=1,
#     areastyle_opts=opts.AreaStyleOpts(opacity=0.5),
#     linestyle_opts=opts.LineStyleOpts(),
#     label_opts=opts.LabelOpts(is_show=False),
# ).extend_axis(
#     yaxis=opts.AxisOpts(
#         name="Precip(mm)",
#         name_location="start",
#         type_="value",
#         max_=5,
#         is_inverse=True,
#         axistick_opts=opts.AxisTickOpts(is_show=True),
#         splitline_opts=opts.SplitLineOpts(is_show=True),
#     )
# ).set_global_opts(
#     title_opts=opts.TitleOpts(
#         title="LineChart",
#         subtitle="With zoom",
#         pos_left="center",
#         pos_top="top",
#     ),
#     tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross"),
#     legend_opts=opts.LegendOpts(pos_left="left"),
#     datazoom_opts=[
#         opts.DataZoomOpts(range_start=0, range_end=100),
#         opts.DataZoomOpts(type_="inside", range_start=0, range_end=100),
#     ],
#     xaxis_opts=opts.AxisOpts(type_="category", boundary_gap=False),
#     yaxis_opts=opts.AxisOpts(name="Some speed(m^3/s)", type_="value", max_=500),
# ).set_series_opts(
#     markarea_opts=opts.MarkAreaOpts(
#         is_silent=False,
#         data=[
#             opts.MarkAreaItem(
#                 name="Some name",
#                 x=("2009/9/12-7:00", "2009/9/22-7:00"),
#                 label_opts=opts.LabelOpts(is_show=False),
#                 itemstyle_opts=opts.ItemStyleOpts(color="#DCA3A2", opacity=0.5),
#             ),
#             opts.MarkAreaItem(
#                 name="降雨量",
#                 x=("2009/9/10-7:00", "2009/9/20-7:00"),
#                 label_opts=opts.LabelOpts(is_show=False),
#                 itemstyle_opts=opts.ItemStyleOpts(color="#A1A9AF", opacity=0.5),
#             ),
#         ],
#     ),
#     axisline_opts=opts.AxisLineOpts(),
# ).render("rainfall.html")

url = "http://94.154.11.74/frost/v1.1/"
service = fsc.SensorThingsService(url)
date_range_start = arrow.utcnow().shift(days=-3).format('YYYY-MM-DD')
date_range_end = arrow.utcnow().format('YYYY-MM-DD')

MDT = service.multi_datastreams().find('RudnMeteoRawDataMultiStream')
def FrostFilterQueryStringByDate(start_date, end_date):
    filter_query_string = "phenomenonTime ge {0}T00:00:00+00:00 and phenomenonTime lt {1}T00:00:00+00:00".format(start_date,end_date)
    return(filter_query_string)

def GetFrostDataRUDNMeteo(MDT,start_date,end_date):
    filter_query_string = FrostFilterQueryStringByDate(start_date,end_date)
    Observations = MDT.get_observations().query()
    Observations = Observations.filter(filter_query_string).list()
    result_list = []
    for observation in Observations:
        result_list.append(observation.result+[arrow.get(observation.phenomenon_time).to('Europe/Moscow').format('YYYY-MM-DD HH:mm:ss')])
    return result_list

def FrostDataRUDNMeteoToDataFrame(result_list):
    df = pd.DataFrame(result_list, columns = ['WinDir_min', 'WinDir_mean','WinDir_max',
                                        'WinSpeed_min','WinSpeed_mean','WinSpeed_max',
                                        'Tair','RH','P_atm','Pcum','Timestamp']) 
    return(df)

def graph_update():
    result_list = GetFrostDataRUDNMeteo(MDT, date_range_start, date_range_end)
    echart_line_graph_draw.refresh(result_list)
#def update_dates(cache, value, index):
#    cache[index]=value

@ui.refreshable
def echart_line_graph_draw(all_data) -> None:
    ui.echart.from_pyecharts(
        Line()
        .add_xaxis(xaxis_data=[item[10] for item in all_data])
        .add_yaxis(
            series_name="Температура воздуха, С",
            y_axis=[item[6] for item in all_data],
            yaxis_index=0,
            is_smooth=False,
            is_symbol_show=False,
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title="Метеостанция АТИ РУДН"),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
            datazoom_opts=[
                opts.DataZoomOpts(xaxis_index=0, yaxis_index=1),
                opts.DataZoomOpts(type_="slider"),
                opts.DataZoomOpts(orient="vertical", pos_left=20)
            ],
            visualmap_opts=opts.VisualMapOpts(
                pos_top="10",
                pos_right="10",
                is_piecewise=True,
                pieces=[
                    {"gt":  0, "lte":  5, "color": "#137cd1"},
                    {"gt":  5, "lte": 10, "color": "#08d0e7"},
                    {"gt": 10, "lte": 15, "color": "#0ef6df"},
                    {"gt": 15, "lte": 20, "color": "#19c485"},
                    {"gt": 20, "lte": 30, "color": "#249138"},
                    {"gt": 30,            "color": "#d97b1c"},
                ],
                out_of_range={"color": "#999"},
            ),
            xaxis_opts=opts.AxisOpts(type_="category"),
            yaxis_opts=opts.AxisOpts(
                type_="value",
                name_location="start",
                is_scale=True,
                axistick_opts=opts.AxisTickOpts(is_inside=False),
            ),
        )
        .set_series_opts(
            markline_opts=opts.MarkLineOpts(
                data=[
                    {"yAxis": 5},
                    {"yAxis": 10},
                    {"yAxis": 15},
                    {"yAxis": 20},
                    {"yAxis": 30},
                ],symbol='none',
                label_opts=opts.LabelOpts(position="end"),
            )
        )
    )
def start_date() -> None:
    with ui.input('Date').bind_value(globals(), 'date_range_start') as date:
        with ui.menu().props('no-parent-event') as menu:
            with ui.date(on_change = graph_update).bind_value(date):
                with ui.row().classes('justify-end'):
                    ui.button('Close', on_click=menu.close).props('flat')
        with date.add_slot('append'):
            ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')
    
def end_date() -> None:
    with ui.input('Date').bind_value(globals(), 'date_range_end') as date:
        with ui.menu().props('no-parent-event') as menu:
            with  ui.date(on_change = graph_update).bind_value(date):
                with ui.row().classes('justify-end'):
                    ui.button('Close', on_click=menu.close).props('flat')
        with date.add_slot('append'):
            ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')
            

#def update_date() 
#    result_list = GetFrostDataRUDNMeteo(MDT, date_range['start'], date_range['end'])
#    echart_line_graph_draw.refresh(result_list)


    
#cache = app.storage.client
# arrow.utcnow().shift(days=-3).format('YYYY-MM-DD')
#arrow.utcnow().format('YYYY-MM-DD')
#print(cache['end_date'])
result_list = GetFrostDataRUDNMeteo(MDT, date_range_start, date_range_end)
with ui.header().classes(replace='row items-center') as header:
    ui.button(on_click=lambda: left_drawer.toggle(), icon='menu').props('flat color=white')
    with ui.tabs() as tabs:
        ui.tab('Метеостанция АТИ РУДН')
        ui.tab('B')
        ui.tab('C')

with ui.footer(value=False) as footer:
    ui.label('Эта штука работает @2024')

with ui.left_drawer().classes('bg-blue-100') as left_drawer:
    ui.label('Какое-то меню')

with ui.page_sticky(position='bottom-right', x_offset=20, y_offset=20):
    ui.button(on_click=footer.toggle, icon='contact_support').props('fab')

with ui.tab_panels(tabs, value='A').classes('w-full'):
    with ui.tab_panel('Метеостанция АТИ РУДН'):
        ui.label('Данные метеостанции')
        with ui.row():
            start_date()
            end_date()
        echart_line_graph_draw(result_list)


    with ui.tab_panel('B'):
        ui.label('Content of B')
    with ui.tab_panel('C'):
        ui.label('Content of C')


ui.run(title="TEST",
       port=8080,
       show=True,
       reload=True,
       root_path="",
       storage_secret="warroom123warroom")

