import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, callback, State, no_update
import dash
import vsl_data as data
import dash_bootstrap_components as dbc
import json
import geopandas as gpd



# Import data variables fom vsl_data
kommune_dict = data.kommune_dict
total_rejser_stationer= data.total_rejser_stationer
# Vi skal benytte UTF-8 til at læse filerne, da vi ellers ikke kan benytte ÆØÅ!!

# Load the data for the map
with open('municipalities.geojson', encoding='utf-8') as f:
    gdf_municipalities = gpd.read_file(f)
gdf_municipalities_grouped = gdf_municipalities.dissolve(
    by='lau_1',
    aggfunc='first'  # Aggregation logic to retain attributes
)
gdf_municipalities_grouped["lau_1"] = gdf_municipalities_grouped.index
geojson_municipalities = json.loads(gdf_municipalities_grouped.to_json())

with open('regioner.geojson', encoding='utf-8') as f:
    gdf_regions = gpd.read_file(f)
gdf_regions_grouped = gdf_regions.dissolve(by='REGIONKODE')
geojson_regions = json.loads(gdf_regions_grouped.to_json())


map_data = pd.read_csv(
    'MapData.csv', delimiter=',', encoding='utf-8',
    dtype={'Kommune Kode': int,'Region':str,'Ankomster':float,'Afrejser':float,'Indbyggertal':float,'Afrejser pr. Indbygger':float,'Ankomster pr. Indbygger':float, 'lat':float, 'lon':float,'Coordinates':str})

map_data['Afrejser pr. Indbygger'] = map_data['Afrejser pr. Indbygger'].fillna(0)
map_data['Ankomster pr. Indbygger'] = map_data['Ankomster pr. Indbygger'].fillna(0)


df_stations = pd.read_csv(
    'filtered_gtfs_stops.csv', delimiter=',', encoding='utf-8',
    names=['stop_id','stop_code','stop_name','stop_desc','stop_lat','stop_lon','location_type','parent_station','wheelchair_boarding','platform_code','total_rejser']  # Added 'Coordinates'
)
df_stations['total_rejser'] = pd.to_numeric(df_stations['total_rejser'], errors='coerce')
df_stations = pd.merge(df_stations, total_rejser_stationer, how='left', left_on='stop_name', right_on='Station')
df_stations= df_stations.drop(columns='Station')

scatter_data = pd.read_csv('scatter_stations_travel_time.csv', sep=',',
                   dtype={'Antal Rejser':int})


# Create dictionary of the colors for the app
colors = {'background_title': 'black',
          'background_app':'whitesmoke',
          'graphs':'orange',
          'text': '#ffffff'}


custom_color = [(0, 'grey'),(0.00001, 'grey'),
                (0.00001,'aliceblue'),(0.1,'lightsteelblue'),(1,'darkblue')]


# Create a dictionary of the regions and region codes
region_code_to_name = {
    "1085": "Region Sjælland",
    "1083": "Region Syddanmark",
    "1081": "Region Nordjylland",
    "1084": "Region Hovedstaden",
    "1082": "Region Midtjylland"
}

regions = ["Region Sjælland", "Region Syddanmark", "Region Nordjylland", "Region Hovedstaden", "Region Midtjylland"]



# Create Dash app
app = Dash(__name__,external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)


# Create the choropleth map
def create_map(type="choropleth_map_region", dataset=map_data, geojsonVal=geojson_regions, center_lat=56.21974050080942, center_lon=11.675033256009756, zoom=5.9, color_column='Afrejser pr. Indbygger',selection = 'Afrejser'):
    if type == "choropleth_map_region":
        return px.choropleth_map(
            dataset, 
            geojson=geojsonVal, 
            locations='Kommune Kode',
            color = color_column,
            color_continuous_scale = custom_color,
            range_color = (0, 1500),
            map_style = "carto-positron",
            zoom = zoom, 
            center = {"lat": center_lat, "lon": center_lon},
            opacity = 0.8,
            hover_name='Region',
            hover_data={'Coordinates':True}
        ).update_layout(
            height = 800, width = 800,
            margin = {"r": 0, "t": 0, "l": 0, "b": 0},
            plot_bgcolor = colors['background_app'],
            paper_bgcolor = colors['background_app']
        )
    elif type == "choropleth_map_municipality":
        return px.choropleth_map(
            dataset, 
            geojson=geojsonVal, 
            locations='Kommune Kode', 
            color = color_column,
            color_continuous_scale = custom_color,
            range_color=(0, 130),
            map_style="carto-positron",
            zoom=zoom, 
            center={"lat": center_lat, "lon": center_lon},
            opacity=0.8,
            hover_name='Kommune',
            hover_data={'Coordinates': True}
        ).update_layout(
            height=800, width=800,
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            plot_bgcolor = colors['background_app'],
            paper_bgcolor = colors['background_app']
        )
    elif type == "scatter_map":
        scatter_fig = px.scatter_map(
            dataset,
            lat='stop_lat',
            lon='stop_lon',
            size_max=15,
            map_style="carto-positron",
            zoom=zoom,
            size= selection,
            center={"lat": center_lat, "lon": center_lon},
            opacity=0.8,
            hover_name='stop_name',
            hover_data= selection
        )

        #scatter_fig.add_scattergeo(
        #    lat=[55.6761, 56.2639], 
        #    lon=[12.5683, 9.5018],
        #    mode='lines',
        #    line=dict(width=2, color='red'),
        #    name="Connections"
        #)

        scatter_fig.update_traces(marker=dict(color=colors['graphs']))
        
        scatter_fig.update_layout(
            height=800, width=800,
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            plot_bgcolor = colors['background_app'],
            paper_bgcolor = colors['background_app'],
        )

        return scatter_fig



# Create bar chart
def create_bar_fig(click_level = 'Hele landet', selection = "Afrejser", data_set = map_data, click_data_map = 'regioner'):
    if selection == 'Afrejser':
        column = 'Afrejser pr. Indbygger'
    elif selection == 'Ankomster':
        column = 'Ankomster pr. Indbygger'
    else: 
        print('Something went wrong. Could not find the column')

    if click_level == 'Hele landet':
        region_codes = list(region_code_to_name.keys())
        region_codes = [int(element) for element in region_codes]
        regioner = data_set.loc[data_set['Kommune Kode'].isin(region_codes)]
        bar_data = go.Bar(x=regioner['Region'], y=regioner[column],marker=dict(color=colors['graphs']),hoverinfo='x')

        bar_fig = go.Figure(data = bar_data)
        bar_fig.update_layout(title = f'Antal {column} for de 5 {click_data_map}',
                              plot_bgcolor = colors['background_app'],
                              paper_bgcolor = colors['background_app'])
        return bar_fig
    
    elif click_level == 'Regioner':
        five_largest = data_set.nlargest(5,column) # municipalities in the region

        y_lim = five_largest[column].values

        bar_data = go.Bar(x=five_largest["Kommune"].values, y=five_largest[column].values, marker=dict(color=colors['graphs']),hoverinfo = 'x')

        bar_fig = go.Figure(data=bar_data, layout = go.Layout(yaxis = dict(range=[0,max(y_lim)+(y_lim/10)])))

        bar_fig.update_layout(title= f'Antal {column} for de 5 travleste kommuner i {click_data_map}',
                              plot_bgcolor = colors['background_app'],
                              paper_bgcolor = colors['background_app'])
        return bar_fig
    
    elif click_level == 'Kommuner':

        five_largest = data_set.nlargest(5,selection) # stations_in_municipality

        y_lim = five_largest[selection].values

        bar_data = go.Bar(x=five_largest["stop_name"].values, y=five_largest[selection].values, marker=dict(color=colors['graphs']),hoverinfo = 'x')

        bar_fig = go.Figure(data=bar_data, layout = go.Layout(yaxis = dict(range=[0,max(y_lim)+(y_lim/10)])))

        bar_fig.update_layout(title= f'Totale antal {selection.lower()} for de {len(five_largest)} travleste stationer i {click_data_map}',
                              plot_bgcolor = colors['background_app'],
                              paper_bgcolor = colors['background_app'])
        return bar_fig
    else:
        print('Something went wrong. Could not find the municipality')



def create_buble_fig(station=None, level='Region', selection ='Afrejser'):
    if level == 'Region' or level == 'Municipality':
        
        buble_placeholder = go.Figure()

        buble_placeholder.update_layout(
            xaxis=dict(showgrid=False, zeroline=False), 
            yaxis=dict(showgrid=False, zeroline=False),
            title="This chart will show when you click on a station",
            plot_bgcolor = colors['background_app'],
            paper_bgcolor = colors['background_app'])
        
        return buble_placeholder

    elif level =='Station':
        station_click = str(station)
        if selection =='Afrejser':
            df_station_click = scatter_data[scatter_data['Fra Station:'] == station_click]
            rejse_station = 'Til Station:'
            titel_tekst = "fra"
        else:
            df_station_click = scatter_data[scatter_data['Til Station:'] == station_click]
            rejse_station= 'Fra Station:'
            titel_tekst = "til"
        
        df_station_click['Gennemsnitlig Rejsetid'] = df_station_click['Gennemsnitlig Rejsetid'].round(2)

        buble_fig = px.scatter(
            df_station_click, 
            x="Gennemsnitlig Rejsetid", # vises ikke helt korret. Skriver k ved tusinder, selvom tallet er tusind
            y="Antal Rejser",
            size='Antal Rejser',
            color_continuous_scale= colors['graphs'],
            title=f"{selection} {titel_tekst} {station} Station",
            #text='Til Station:',
            hover_name= rejse_station,
            labels={"Gennemsnitlig Rejsetid": "Gennemsnitlig Rejsetid (min)", "Antal Rejser": f"Antal rejser"},
            template="plotly"
        )

        # Add labels to the points
        #buble_fig.update_traces(textposition='top center')

        buble_fig.update_layout(plot_bgcolor = colors['background_app'],
                        paper_bgcolor = colors['background_app'])
                            
        return buble_fig
    else:
        print("Something went wrong. Buble_chart function.")
        return None



def reset_app():
    reset_map = create_map(type="choropleth_map_region", dataset=map_data, geojsonVal=geojson_regions, center_lat=56.21974050080942, center_lon=11.675033256009756, zoom=5.9, color_column='Afrejser pr. Indbygger')
    reset_bar = create_bar_fig(click_level = 'Hele landet', selection = "Afrejser", data_set = map_data, click_data_map = 'regioner')
    reset_buble = create_buble_fig(station=None, level='Region')
    reset_context = {'level': 'Region'}
    reset_last_station = None

    return reset_map, reset_bar, reset_buble, reset_context, reset_last_station




# Define components of the dash app
title = html.Div(style={'backgroundColor': colors['background_title']},
                 children=[html.H1(children="Public Transit Usage",
                                   style={'textAlign': 'center','color': colors['text']
                 })])

radio_button = dcc.RadioItems(options=['Afrejser', 'Ankomster'],
                              value='Afrejser', 
                              id= "radio-button", 
                              inline=True,
                              style={'marginTop': 10})

reset_button = dbc.Button("Reset Filter", 
                          color="danger", 
                          outline=True, 
                          id="reset-button", 
                          n_clicks=0,
                          style={'display': 'inline-block',  
                                 'marginTop': 15,
                          })

dk_map = dcc.Graph(
            id = 'map_dk',
            figure = create_map(),
            style = {'height':'800px'})

bar_chart = dcc.Graph(id ='bar-chart',
                      figure = create_bar_fig(),
                      style = {'height': '400px'})

buble_chart = dcc.Graph(id ='buble_chart', 
                       figure = create_buble_fig(),
                       style = {'height': '400px'})




# Adjust the layout of the app
app.layout = html.Div([
    dcc.Store(id='click-context', data={'level': 'Region'}),
    dcc.Store(id='last-selected-station', data=None),
    dcc.Store(id='reset-clicks', data=0),

    dbc.Row([dbc.Col(title, width=14)],
            align = "center",
            style={'backgroundColor':colors['background_app']}),
    
    dbc.Row([
        dbc.Col(radio_button, width=2, align = "left"),
        dbc.Col(width = 8, align = 'center'),
        dbc.Col(reset_button, width=2, align = "right")],
        style={'backgroundColor':colors['background_app']}),
    
    dbc.Row([
        dbc.Col(width = 12, align = 'center')],
        style={'backgroundColor':colors['background_app']}),

    dbc.Row([
        dbc.Col(dk_map, width=6, align = 'left'),
        dbc.Col(dbc.Container([
            dbc.Row(bar_chart, align = 'center'),
            dbc.Row(buble_chart, align = 'center'),

        ]), width = 6, align = 'center')
    ], style={'backgroundColor':colors['background_app']})
])







# Callback for updating the map
@app.callback(
    [Output('map_dk', 'figure'),
     Output('bar-chart','figure'),
     Output('buble_chart','figure'),
     Output('click-context', 'data'),
     Output('last-selected-station', 'data')],
    [Input('reset-clicks', 'data'),
     Input('map_dk', 'clickData'),
     Input('radio-button', 'value'),
     Input('bar-chart','clickData'),],
    [State('click-context', 'data'),
     State('last-selected-station', 'data')])

def update_map_region(reset_clicks,clickData_map, value, clickData_bar, context_level, last_station): 
    
    ctx = dash.callback_context

    current_level = context_level['level']

    
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate


    elif ctx.triggered[0]['prop_id'].startswith("reset-clicks.data"):
            return reset_app()


    elif ctx.triggered[0]["prop_id"].startswith("map_dk.clickData"):
        if clickData_map is None:
            # Reset the app
            return reset_app()
        else:
            try:
                if current_level == "Region":
                    # Municipality level. After the user clicks on a region in the map
                    region_code = str(clickData_map['points'][0]['location'])


                    region_name = region_code_to_name.get(region_code, None)
                    if not region_name:
                        raise ValueError(f"Region code {region_code} not found in mapping.")

                    region_data = map_data[map_data['Region'] == region_name]

                    if region_data.empty:
                        raise ValueError(f"No municipalities found for region {region_name}.")
                    last_row = region_data.iloc[-1] if not region_data.empty else None


                    # DEFINES THE MAP
                    filtered_geojson = {
                        "type": "FeatureCollection",
                        "features": [
                            feature for feature in geojson_municipalities["features"]
                            if feature["properties"]["lau_1"] in str(region_data["Kommune Kode"].values)
                        ]
                    }

                    lat = last_row['lat']
                    lon = last_row['lon']

                    updated_map = create_map(
                        type="choropleth_map_municipality",
                        dataset=region_data,
                        geojsonVal=filtered_geojson,
                        center_lat=lat,
                        center_lon=lon,
                        zoom=7.1
                    )
                    

                    # DEFINES THE BAR CHART
                    bar_data = region_data.iloc[:-1,:]
                    updated_bar = create_bar_fig(data_set=bar_data, click_level = 'Regioner', selection= value, click_data_map = region_name)


                    # DEFINES THE BUBLE CHART
                    updated_buble = create_buble_fig(level="Region")


                    # DEFINES THE NEW CONTEXT
                    new_context = {'level': 'Municipality'}

                    return updated_map, updated_bar, updated_buble, new_context, last_station
                
                elif current_level == "Municipality":
                    # Station level. After the user clicks on a municipality in the map
                        
                    municipality_name =str(clickData_map['points'][0]['hovertext'])
                    
                    region_data = map_data[map_data['Kommune'] == municipality_name]
                    

                    last_row = region_data.iloc[-1] if not region_data.empty else None

                    lat = last_row['lat']
                    lon = last_row['lon']

                    kommune_stationer = data.kommune_dict.get(municipality_name, None)


                    # DEFINES THE MAP
                    df_stations_filtered = df_stations[df_stations['stop_name'].isin(kommune_stationer)]

                    updated_map = create_map(
                        type="scatter_map",
                        dataset=df_stations_filtered,
                        center_lat=lat,
                        center_lon=lon,
                        zoom=9.9
                    )


                    # DEFINES THE BAR CHART
                   
                    updated_bar = create_bar_fig(data_set = df_stations_filtered, click_level = 'Kommuner', selection= value, click_data_map = municipality_name)


                    # DEFINES THE BUBLE CHART
                    updated_buble = create_buble_fig(level="Municipality")


                    # DEFINES THE NEW CONTEXT
                    new_context = {'level': 'Station'}

                    return updated_map, updated_bar, updated_buble, new_context, last_station

                elif current_level == "Station": # If the user clicks on a station
                    current_station = str(clickData_map['points'][0]['hovertext'])

                    if current_station == last_station:
                        # Reset the app
                        return reset_app()
                    else:
                        # DEFINES THE BUBLE CHART
                        updated_buble = create_buble_fig(station=current_station, level='Station')
                        
                        return no_update, no_update, updated_buble, context_level, last_station

                else:
                    print("Something went wrong in the map")
                    return reset_app()
                
            except Exception as e:
                print(f"Error: {str(e)}")
                print(f'clickData_map looks like this: {clickData_map}')
                return reset_app()

    elif ctx.triggered[0]["prop_id"].startswith("bar-chart.clickData"):
        if clickData_bar is None:
            # Reset the app
            return reset_app()
        else:
            try:
                if current_level == "Region":
                    # Municipality level. After the user clicks on a region in the bar chart
                    region_name = str(clickData_bar['points'][0]['x'])

                    region_data = map_data[map_data['Region'] == region_name]

                    if region_data.empty:
                        raise ValueError(f"No municipalities found for region {region_name}.")
                    
                    last_row = region_data.iloc[-1] if not region_data.empty else None

                    # DEFINES THE MAP
                    filtered_geojson = {
                        "type": "FeatureCollection",
                        "features": [
                            feature for feature in geojson_municipalities["features"]
                            if feature["properties"]["lau_1"] in str(region_data["Kommune Kode"].values)
                        ]
                    }

                    lat = last_row['lat']
                    lon = last_row['lon']

                    updated_map = create_map(
                        type="choropleth_map_municipality",
                        dataset=region_data,
                        geojsonVal=filtered_geojson,
                        center_lat=lat,
                        center_lon=lon,
                        zoom=7.1
                    )
             

                    # DEFINES THE BAR CHART
                    bar_data = region_data.iloc[:-1,:]
                    updated_bar = create_bar_fig(click_level = 'Regioner', selection = value, data_set = bar_data, click_data_map = region_name)


                    # DEFINES THE BUBLE CHART
                    updated_buble = create_buble_fig(level="Region")


                    # DEFINES THE NEW CONTEXT
                    new_context = {'level': 'Municipality'}

                    return updated_map, updated_bar, updated_buble, new_context, last_station
                

                elif current_level == "Municipality": 
                    # Station level. After the user clicks on a municipality in the bar chart

                    municipality_name = str(clickData_bar['points'][0]['x'])

                    municipality_data = map_data[map_data['Kommune'] == municipality_name]

                    if municipality_data.empty:
                        raise ValueError(f"No stations found for municipality {municipality_name}.")

                    last_row = municipality_data.iloc[-1] if not municipality_data.empty else None

                    lat = last_row['lat']
                    lon = last_row['lon']

                    kommune_stationer = data.kommune_dict.get(municipality_name, None)


                    # DEFINES THE MAP
                    df_stations_filtered = df_stations[df_stations['stop_name'].isin(kommune_stationer)]
                    

                    updated_map = create_map(
                        type="scatter_map",
                        dataset=df_stations_filtered,
                        center_lat=lat,
                        center_lon=lon,
                        zoom=9.9,
                        selection = value
                     )

                    # DEFINES THE BAR CHART
                    updated_bar = create_bar_fig(click_level = 'Kommuner', selection = value, data_set = df_stations_filtered, click_data_map = municipality_name)


                    # DEFINES THE BUBLE CHART
                    updated_buble = create_buble_fig(level="Municipality")


                    # DEFINES THE NEW CONTEXT
                    new_context = {'level': 'Station'}

                    return updated_map, updated_bar, updated_buble, new_context, last_station

                elif current_level == "Station": # If the user clicks on a station
                    current_station= str(clickData_bar['points'][0]['x'])

                    if current_station == last_station:
                        # Reset the app
                        return reset_app()
                    else:
                        # DEFINES THE BUBLE CHART
                        updated_buble = create_buble_fig(station=current_station, level='Station', selection= value)

                        return no_update, no_update, updated_buble, context_level, last_station

                else:
                    print("Something went wrong in the bar chart")
                    return reset_app()
                
            except Exception as e:
                print(f"Error: {str(e)}")
                print(f'clickData_bar looks like this: {clickData_bar}')
                return reset_app()
    else:
        print("Something went wrong. Reload the app")
        return reset_app()



# Callback for clicking the reset-button
@app.callback(
    [Output('reset-clicks', 'data'),
     Output('radio-button', 'value')],
    Input('reset-button', 'n_clicks'),
    prevent_initial_call=True
)
def update_reset_clicks(n_clicks):
    # If the user clicks on the reset button, the n_clicks updates
    if n_clicks:
        print(f"Reset button clicked {n_clicks} times")
        return 0, 'Afrejser'
    raise dash.exceptions.PreventUpdate




# Kør serveren
if __name__ == '__main__':
    app.run_server(debug=True)
