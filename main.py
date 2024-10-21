#!/usr/bin/env python3
from nicegui import app, ui
import frost_sta_client as fsc
import pandas as pd
import arrow


url = "http://94.154.11.74/frost/v1.1/"
service = fsc.SensorThingsService(url)
date_range_start = arrow.utcnow().shift(days=-3).format('YYYY-MM-DD')
date_range_end = arrow.utcnow().format('YYYY-MM-DD')
result_list = []
var_index = 0

MDT = service.multi_datastreams().find('RudnMeteoRawDataMultiStream')
def FrostFilterQueryStringByDate(start_date, end_date):
    filter_query_string = "phenomenonTime ge {0}T00:00:00+00:00 and phenomenonTime lt {1}T00:00:00+00:00".format(start_date,end_date)
    return(filter_query_string)

def GetFrostDataRUDNMeteo(MDT,start_date,end_date):
    filter_query_string = FrostFilterQueryStringByDate(start_date,end_date)
    Observations = MDT.get_observations().query()
    Observations = Observations.filter(filter_query_string).list(callback=ui_callback_func, step_size=1000)
    result_list = []
    for observation in Observations:
        result_list.append(observation.result+[int(arrow.get(observation.phenomenon_time).to('Europe/Moscow').timestamp()*1000),
                                               arrow.get(observation.phenomenon_time).to('Europe/Moscow').format('YYYY-MM-DD HH:mm:ss')])

    
    return result_list

def FrostDataRUDNMeteoToDataFrame(result_list):
    df = pd.DataFrame(result_list, columns = ['WinDir_min', 'WinDir_mean','WinDir_max',
                                              'WinSpeed_min','WinSpeed_mean','WinSpeed_max',
                                              'Tair','RH','P_atm','Pcum','Timestamp','DateTime']) 
    return(df.to_csv(lineterminator='\r\n', index=False))

def graph_update():
    global_list = globals()
    all_data = global_list['result_list']
    var_index = global_list['var_index']
    print(len(result_list))
    notification_list = ['','Строим график скорости ветра','',
                         '','Строим график направления ветра','',
                         'Строим график температуры воздуха',
                         'Строим график влажности воздуха',
                         'Строим график атмосферного давления',
                         'Строим график кумуляты осадков'] 
    ui.notify(notification_list[var_index])
    echart_line_graph_draw.refresh(all_data,var_index)
    
def update_var_index(upd_var_index):
    global_list = globals()
    global_list['var_index'] = upd_var_index
    graph_update()


def get_data_from_frost():
    global_list = globals()
    global_list['result_list'] = []
    global_list['result_list']= GetFrostDataRUDNMeteo(MDT, date_range_start, date_range_end)
    graph_update()

def ui_callback_func(loaded_entities):
    ui.notify("Более {} строчек загружено!".format(loaded_entities))

@ui.refreshable
# Переписать нахер на классический echarts - pyechart - говно
def echart_line_graph_draw(all_data,var_index) -> None:

    axis_name_list =['','Направление ветра, град','', 
                    '','Скорость ветра, м/с','', 
                    'Температура воздуха, С', 
                    'Влажность воздуха, %', 
                    'Атмосферное давление, гПа', 
                    'Кумулята осадков, мм','UnixTime','Дата']
    print(all_data)

    graph_object = {
          'dataset': {
            'source':all_data,
            'dimensions': axis_name_list,
        },
        'title': {
            'left': 'center',
            'text': axis_name_list[var_index]
        },
        'toolbox': {
            'feature': {
            'dataZoom': {
                'yAxisIndex': 'none'
            },
            'restore': {},
            'saveAsImage': {}
            }
        },
        'xAxis': {
            #'type':'category',
            'type':'time',
            'axisLabel': {
                'formatter': '{yyyy}-{MM}-{dd} {HH}:{mm}'
            }
        },
        'yAxis': {
            'type': 'value',
             'min': 'dataMin', 
             'max': 'dataMax'
        },
        'dataZoom': [
            {
                'type': 'slider',
                'xAxisIndex': 0,

                },
                {
                'type': 'slider',
                'yAxisIndex': 0,
                'left': 20,

                },
                {
                'type': 'inside',
                'xAxisIndex': 0,

                },
                {
                'type': 'inside',
                'yAxisIndex': 0,

                }
        ],
        'series': [
            {
            'name': axis_name_list[var_index],
            'type': 'line',
            'symbol': 'none',
            'smooth': 'false',
            'encode': {
                'x': axis_name_list[10],
                'y': axis_name_list[var_index]
            }
            }
        ]
    }
    ui.echart(graph_object).style('height: 26rem')
    #ui.echart.from_pyecharts(graph_object).props("height=600px")
def start_date_select_ui() -> None:
    with ui.input('Дата начала периода').bind_value(globals(), 'date_range_start') as date:
        with ui.menu().props('no-parent-event') as menu:
            with ui.date().bind_value(date):
                with ui.row().classes('justify-end'):
                    ui.button('Close', on_click=menu.close).props('flat')
        with date.add_slot('append'):
            ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')
    
def end_date_select_ui() -> None:
    with ui.input('Дата окончания периода').bind_value(globals(), 'date_range_end') as date:
        with ui.menu().props('no-parent-event') as menu:
            with  ui.date().bind_value(date):
                with ui.row().classes('justify-end'):
                    ui.button('Close', on_click=menu.close).props('flat')
        with date.add_slot('append'):
            ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')
            
def download_csv_button() -> None:
    ui.button('Скачать данные как csv', 
              on_click=lambda: ui.download(
                  bytes(FrostDataRUDNMeteoToDataFrame(result_list), encoding='utf-8'), filename="output.csv"
                  )
    )



    
#cache = app.storage.client
# arrow.utcnow().shift(days=-3).format('YYYY-MM-DD')
#arrow.utcnow().format('YYYY-MM-DD')
#print(cache['end_date'])
get_data_from_frost()
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
    start_date_select_ui()
    end_date_select_ui()
    ui.button('Получить данные', on_click=get_data_from_frost)
    download_csv_button()


with ui.page_sticky(position='bottom-right', x_offset=20, y_offset=20):
    ui.button(on_click=footer.toggle, icon='contact_support').props('fab')

with ui.tab_panels(tabs, value='Метеостанция АТИ РУДН').classes('w-full'):
    with ui.tab_panel('Метеостанция АТИ РУДН'):
        with ui.dropdown_button('Отобразить на графике', auto_close=True):
            ui.item('Скорость ветра, м/с', on_click=lambda: update_var_index(4))
            ui.item('Направление ветра, град', on_click=lambda: update_var_index(1))
            ui.item('Температура воздуха, С', on_click=lambda: update_var_index(6))
            ui.item('Влажность воздуха, %', on_click=lambda: update_var_index(7))
            ui.item('Атмосферное давление, гПа', on_click=lambda: update_var_index(8))
            ui.item('Кумулята осадков, м', on_click=lambda: update_var_index(9))
        echart_line_graph_draw(result_list,var_index)
    with ui.tab_panel('B'):
        ui.label('Content of B')
    with ui.tab_panel('C'):
        ui.label('Content of C')


ui.run(title="Тестирования тестирования",
       port=8080,
       show=True,
       reload=True,
       root_path="",
       storage_secret="warroom123warroom")

