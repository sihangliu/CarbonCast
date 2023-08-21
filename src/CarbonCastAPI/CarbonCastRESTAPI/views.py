from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
# from .models import CarbonCast
# from .serializers import CarbonCastSerializer
from .helper import get_latest_csv_file, get_actual_value_file_by_date, get_CI_forecasts_csv_file, get_energy_forecasts_csv_file
import os
from datetime import datetime
# import json

#Defining a list of US region codes
US_region_codes = ['AECI','AZPS', 'BPAT','CISO', 'DUK', 'EPE', 'ERCO', 'FPL', 
                'ISNE', 'LDWP', 'MISO', 'NEVP', 'NWMT', 'NYIS', 'PACE', 'PJM', 
                'SC', 'SCEG', 'SOCO', 'TIDC', 'TVA']

# 1: 
class CarbonIntensityApiView(APIView):
    # add permission to check if user is authenticated: permissions.IsAuthenticated
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        
        region_code = request.query_params.get('regionCode', '')

        csv_file1, csv_file2 = get_latest_csv_file(region_code)
        with open(csv_file1) as file:
            for line in file:
                pass
        values_csv1 = line.split(',')
        with open(csv_file2) as file:
            for line in file:
                pass
        values_csv2 = line.split(',')

        response_data= {
            "UTC time" : values_csv1[1],
            "creation_time (UTC)": values_csv1[2],
            "version": values_csv1[3],
            "region_code": region_code,
            "carbon_intensity_avg_lifecycle": float(values_csv1[4]),
            "carbon_intensity_avg_direct": float(values_csv2[4]),
            "carbon_intensity_unit": "gCO2eg/kWh"                 
          }
        response = {
            "data": response_data
        }
        return Response(response, status=status.HTTP_200_OK)
        
#2    
class EnergySourcesApiView(APIView):
    # add permission to check if user is authenticated: permissions.IsAuthenticated
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        
        region_code = request.query_params.get('regionCode', '')

        csv_file1, csv_fil2 = get_latest_csv_file(region_code)
        with open(csv_file1) as file:
            header = file.readline().strip()
            columns = header.split(',')
            for row in file:
                line = row.strip().split(',')

        fields = [
                 "UTC time", "creation_time (UTC)", "version", "region_code", "coal", "nat_gas", "nuclear",
                 "oil", "hydro", "solar", "wind", "other"
                 ]
        response_data = {}

        for field in fields:
            if field in columns:
                index = columns.index(field)
                value = line[index].strip() if index < len(line) else "0"
                response_data[field] = value
            elif field == "region_code":
                response_data[field] = region_code
            else:
                response_data[field] = "0"
                
        response = {
            "data": response_data
        }
        return Response(response, status=status.HTTP_200_OK)
        
#3    
class CarbonIntensityHistoryApiView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        
        region_code = request.query_params.get('regionCode', '')
        date = request.query_params.get('date', '')
        
        csv_file_a, csv_file_b = get_actual_value_file_by_date(region_code, date)
        print("In view: ", csv_file_a, csv_file_b)
        with open(csv_file_a) as file:
            lines_csv1 = file.readlines()

        with open(csv_file_b) as file:
            lines_csv2 = file.readlines()            

        field_names = [
                        "UTC time", "creation_time (UTC)", "version", "region_code", "carbon_intensity_avg_lifecycle", 
                        "carbon_intensity_avg_direct", "carbon_intensity_unit"
        ]

        values_csv1 = [line.strip().split(',') for line in lines_csv1]
        values_csv2 = [line.strip().split(',') for line in lines_csv2]

        final_list =[]
        for i in range(1,len(values_csv1)):
            temp_dict= {}
            temp_dict[field_names[0]] = values_csv1[i][1]
            temp_dict[field_names[1]] = values_csv1[i][2]
            temp_dict[field_names[2]] = values_csv1[i][3]
            temp_dict[field_names[3]] = region_code
            temp_dict[field_names[4]] = float(values_csv1[i][4])
            temp_dict[field_names[5]] = float(values_csv2[i][4])
            temp_dict[field_names[6]] = "gCO2eg/kWh"
            final_list.append(temp_dict)
        response = {
            "data": final_list
        }
        return Response(response, status=status.HTTP_200_OK)
        
#4    
class EnergySourcesHistoryApiView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        
        region_code = request.query_params.get('regionCode', '')
        date = request.query_params.get('date', '')
        
        csv_file_a, csv_file_b = get_actual_value_file_by_date(region_code, date)
        with open(csv_file_a) as file:
            lines_csv1 = file.readlines()

        with open(csv_file_b) as file:
            lines_csv2 = file.readlines()

        values_csv1 = [line.strip().split(',') for line in lines_csv1]
        values_csv2 = [line.strip().split(',') for line in lines_csv2]

        fields = [
                "UTC time", "creation_time (UTC)", "version","region_code", "coal", "nat_gas", "nuclear",
                "oil", "hydro", "solar", "wind", "other"
            ]
        final_list = []

        for i in range(1, len(values_csv1)):
            temp_dict = {field: "0" for field in fields}
            temp_dict["UTC time"] = values_csv1[i][1]
            temp_dict["creation_time (UTC)"] = values_csv1[i][2]
            temp_dict["version"] = values_csv1[i][3]
            temp_dict["region_code"] = region_code

            for field in fields[2:]:  
                if field in values_csv1[0]:
                    index = values_csv1[0].index(field)
                    temp_dict[field] = values_csv1[i][index]

            final_list.append(temp_dict)


        response = {
            "data": final_list
        }
        return Response(response, status=status.HTTP_200_OK)

#5
class CarbonIntensityForecastsApiView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        region_code = request.query_params.get('regionCode', '')  
        f = request.query_params.get('forecastPeriod', '24h')

        final_interval = int(f[:-1])
        forecastPeriod = int(final_interval)

        today_date = datetime.now().strftime('%Y-%m-%d')
        # date = '2023-08-20'

        CI_lifecycle, CI_direct = get_CI_forecasts_csv_file(region_code, today_date)
        with open(CI_lifecycle) as file:
            lines_CI_lifecycle = file.readlines()

        with open(CI_direct) as file:
            lines_CI_direct = file.readlines()

        field_names = [
                        "UTC time", "creation_time (UTC)", "version", "region_code", "carbon_intensity_avg_lifecycle", 
                        "carbon_intensity_avg_direct", "carbon_intensity_unit"
        ]

        CI_lifecycle_filtered = [line.split(',') for i, line in enumerate(lines_CI_lifecycle) if i>0 and i<=forecastPeriod]
        CI_direct_filtered = [line.split(',') for i, line in enumerate(lines_CI_direct) if i>0 and i<= forecastPeriod]

        final_list =[]
        for i in range(0,len(CI_lifecycle_filtered)):
            temp_dict= {}
            temp_dict[field_names[0]] = CI_lifecycle_filtered[i][0]
            temp_dict[field_names[1]] = CI_lifecycle_filtered[i][1]
            temp_dict[field_names[2]] = CI_lifecycle_filtered[i][2]
            temp_dict[field_names[3]] = region_code
            temp_dict[field_names[4]] = float(CI_lifecycle_filtered[i][3])
            temp_dict[field_names[5]] = float(CI_direct_filtered[i][3])
            temp_dict[field_names[6]] = "gCO2eg/kWh"
            final_list.append(temp_dict)

        response = {
            "data": final_list
        }
        
        return Response(response, status=status.HTTP_200_OK)

#6    
class CarbonIntensityForecastsHistoryApiView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        
        region_code = request.query_params.get('regionCode', '')
        date = request.query_params.get('date', '')
        csv_file_l, csv_file_d = get_CI_forecasts_csv_file(region_code, date)
        with open(csv_file_l) as file:
            lines_csv1 = file.readlines()

        with open(csv_file_d) as file:
            lines_csv2 = file.readlines()

        field_names = [
                        "UTC time", "creation_time (UTC)", "version", "region_code", "forecasted_avg_carbon_intensity_lifecycle", 
                        "forecasted_avg_carbon_intensity_direct", "carbon_intensity_unit"
        ]

        filtered_data_by_date_csv1 = [line.split(',') for line in lines_csv1 if line.startswith(date)]
        filtered_data_by_date_csv2 = [line.split(',') for line in lines_csv2 if line.startswith(date)]

        final_list =[]
        for i in range(0,len(filtered_data_by_date_csv1)):
            temp_dict= {}
            temp_dict[field_names[0]] = filtered_data_by_date_csv1[i][0]
            temp_dict[field_names[1]] = filtered_data_by_date_csv1[i][1]
            temp_dict[field_names[2]] = filtered_data_by_date_csv1[i][2]
            temp_dict[field_names[3]] = region_code
            temp_dict[field_names[4]] = float(filtered_data_by_date_csv1[i][3])
            temp_dict[field_names[5]] = float(filtered_data_by_date_csv2[i][3])
            temp_dict[field_names[6]] = "gCO2eg/kWh"
            final_list.append(temp_dict)
        response = {
            "data": final_list
        }
        return Response(response, status=status.HTTP_200_OK)

#7
class EnergySourcesForecastsHistoryApiView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        region_code = request.query_params.get('regionCode', '')   
        date = request.query_params.get('date', '')
        f = request.query_params.get('forecastPeriod', '24h')

        final_interval = int(f[:-1])
        forecastPeriod = int(final_interval)        

        energy_forecast_csv_file = get_energy_forecasts_csv_file(region_code, date)

        with open(energy_forecast_csv_file) as file:
            lines_csv = file.readlines()

        energy_forecast_filtered_file = [line.split(',') for i, line in enumerate(lines_csv) if i>0 and i<=forecastPeriod]

        fields = [
                "UTC time", "creation_time (UTC)", "version","region_code", "avg_coal_production_forecast", "avg_nat_gas_production_forecast",
                "avg_nuclear_production_forecast", "avg_oil_production_forecast", "avg_hydro_production_forecast", "avg_solar_production_forecast",
                "avg_wind_production_forecast", "avg_other_production_forecast"
            ]

        final_list = []
        for i in range(0, len(energy_forecast_filtered_file)):
            temp_dict = {field: "0" for field in fields}
            temp_dict["UTC time"] = energy_forecast_filtered_file[i][0]
            temp_dict["creation_time (UTC)"] = energy_forecast_filtered_file[i][1]
            temp_dict["version"] = energy_forecast_filtered_file[i][2]
            temp_dict["region_code"] = region_code

            splitlines = lines_csv[0].split(",")
            splitlines[-1] = splitlines[-1].rstrip("\n")
            for field in fields[4:]:  
                if field in lines_csv[0]:
                    index1 = splitlines.index(field)
                    temp_dict[field] = energy_forecast_filtered_file[i][index1]

            final_list.append(temp_dict)

        response = {
                "data": final_list
            }
        return Response(response, status=status.HTTP_200_OK)

#8
class SupportedRegionsApiView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        items = os.listdir("../../real_time")
        supported_regions = [item for item in items if os.path.isdir(os.path.join("../../real_time", item)) and item != 'weather_data']
        response = {
            "US_supported_regions": supported_regions
        }
        return Response(response, status=status.HTTP_200_OK)