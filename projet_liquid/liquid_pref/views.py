from django import http
from django.http.response import JsonResponse
from matplotlib.pyplot import step
from pandas.core import series
from . import computations
from django.shortcuts import render
from django.http import HttpResponse
import json
from django import forms
from django.contrib.postgres.forms import SimpleArrayField
import distutils
from distutils import util
from wsgiref.util import FileWrapper
import xlsxwriter
import pandas as pd
from io import BytesIO as IO





investors_global = []
series_global = [] 
shares_global = [] 
options_holders_global = [] 
options_class_global = [] 
options_global = []
cap_table_global = []
liquid_pref_global = []
shares_prices_global = []
options_prices_global = []

first_step_global = "Nominal"
carve_out_rate_global = 20
participating_global = True
sale_price_global = 100000000
multiples_pref_global = [1,1,1]

floor_global = 10000000
ceiling_global = 200000000
step_global = 1000000
data_table_global = []

class NewForm(forms.Form):
    first_step = forms.ChoiceField(choices=(
    ("Nominal", "Nominal"),
    ("Carve-out", "Carve-out"),
    ))
    carve_out_rate = forms.IntegerField(label="Carve-out rate (%)", initial=20, widget=forms.NumberInput(attrs={'style': 'width:60px'}))
    participating = forms.ChoiceField(choices = (
    (True, "Yes"),
    (False, "No"),
    ))
    sale_price = forms.FloatField(label="Sale price (€)", initial=100000000, widget=forms.NumberInput(attrs={'style': 'width:150px'}))
    multiples_pref = SimpleArrayField(forms.CharField(max_length=100), initial=[1,1,1])

class NewFormPlot(forms.Form):
    floor = forms.IntegerField(label="Minimum", initial=10000000, widget=forms.NumberInput(attrs={'style': 'width:150px'}))
    ceiling = forms.IntegerField(label="Maximum", initial=200000000, widget=forms.NumberInput(attrs={'style': 'width:150px'}))
    step = forms.IntegerField(label="Step", initial=1000000, widget=forms.NumberInput(attrs={'style': 'width:150px'}))

def cap_table_post_traitement(request):
    request_list = list(request.POST.dict().keys())
    res = json.loads(request_list[0])

    shares_list = (res.get("data_shares"))

    series = shares_list[0][1:]
    investors = []
    shares = []

    for i in shares_list[1:]:
        investors.append(i[0])
        shares.append(i[1:])

    options_list = (res.get("data_options"))

    options_class = options_list[0][1:]
    options_holders = []
    options = []

    for i in options_list[1:]:
        options_holders.append(i[0])
        options.append(i[1:])
    
    count = 0
    for i in shares:
        shares[count] = list(map(int, i))
        count = count + 1

    count = 0
    for i in options:
        options[count] = list(map(int, i))
        count = count + 1

    shares_prices = (res.get("data_shares_prices"))[1][1:]
    options_prices = (res.get("data_options_prices"))[1][1:]
    
    return (investors, series, shares, options_holders, options_class, options, shares_prices, options_prices)


# Create your views here.
def index(request):
    if request.method == "POST":
        investors, series, shares, options_holders, options_class, options, shares_prices, options_prices = cap_table_post_traitement(request)
        cap_table, cap_table_styled = computations.cap_table_function(investors, series, shares, options_holders, options_class, options)

        global investors_global, series_global, shares_global, options_holders_global, options_class_global, options_global, cap_table_global, shares_prices_global, options_prices_global
        investors_global = investors
        series_global = series 
        shares_global = shares
        options_holders_global = options_holders
        options_class_global = options_class
        options_global = options
        cap_table_global = cap_table
        shares_prices_global = list(map(float,shares_prices))
        options_prices_global = list(map(float,options_prices))

        return HttpResponse(cap_table_styled.render().replace("<table ", "<table class='table table-hover table-striped' "))
    return render(request, "liquid_pref/index.html", {
        "form": NewForm(),
        "form_plot": NewFormPlot()
    })

def generate(request):
    if request.method == "POST":
        form = NewForm(request.POST)
        if form.is_valid():
            first_step = form.cleaned_data["first_step"]
            carve_out_rate = form.cleaned_data["carve_out_rate"]
            participating = bool(distutils.util.strtobool(form.cleaned_data["participating"]))
            sale_price = form.cleaned_data["sale_price"]
            multiples_pref = list(map(int,form.cleaned_data["multiples_pref"]))


            global first_step_global, carve_out_rate_global, participating_global, sale_price_global, multiples_pref_global
            first_step_global = first_step
            carve_out_rate_global = carve_out_rate
            participating_global = participating
            sale_price_global = sale_price
            multiples_pref_global = multiples_pref

            message="Saved"
        
        return HttpResponse(json.dumps(message))

def plot_parameters(request):
    if request.method == "POST":
        form = NewFormPlot(request.POST)
        if form.is_valid():
            floor = form.cleaned_data["floor"]
            ceiling = form.cleaned_data["ceiling"]
            step = form.cleaned_data["step"]

            global floor_global, ceiling_global, step_global
            floor_global = floor
            ceiling_global = ceiling
            step_global = step

            message="Saved"

        return HttpResponse(json.dumps(message))


def display(request):
    liquid_pref, liquid_pref_styled = computations.liquid_pref_function(cap_table_global, series_global, investors_global, options_holders_global, options_class_global, first_step_global, carve_out_rate_global, multiples_pref_global, participating_global, shares_prices_global, sale_price_global)
    global liquid_pref_global
    liquid_pref_global = liquid_pref
    return HttpResponse(liquid_pref_styled.render().replace("<table ", "<table class='table table-hover table-striped' "))

def plot_graph(request):
    plot_div = computations.plot_liquid_pref(cap_table_global, series_global, investors_global, options_holders_global, options_class_global, first_step_global, carve_out_rate_global, multiples_pref_global, participating_global, shares_prices_global, floor_global, ceiling_global, step_global)
    return JsonResponse(plot_div, safe=False)

def data_table(request):
    df, df_styled = computations.compute_data_table(cap_table_global, series_global, investors_global, options_holders_global, options_class_global, first_step_global, carve_out_rate_global, multiples_pref_global, participating_global, shares_prices_global, floor_global, ceiling_global, step_global)
    global data_table_global
    data_table_global = df
    return HttpResponse(df_styled.render().replace("<table ", "<table class='table table-hover table-striped' "))

def download_cap_table(request):
    excel_file = IO()
    xlwriter = pd.ExcelWriter(excel_file, engine='xlsxwriter')
    cap_table_global.to_excel(xlwriter, 'cap_table')
    workbook  = xlwriter.book
    worksheet = xlwriter.sheets['cap_table']
    format = workbook.add_format({'num_format': '0.00%'})
    worksheet.set_column(len(series_global)+2, len(series_global)+2, None, format)
    worksheet.set_column(len(series_global+options_class_global)+4, len(series_global+options_class_global)+4, None, format)
    xlwriter.save()
    xlwriter.close()
    excel_file.seek(0)
    response = HttpResponse(excel_file.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=cap_table.xlsx'
    return response

def download_liquid_pref(request):
    excel_file = IO()
    xlwriter = pd.ExcelWriter(excel_file, engine='xlsxwriter')
    liquid_pref_global.to_excel(xlwriter, 'liquid_pref')
    workbook  = xlwriter.book
    worksheet = xlwriter.sheets['liquid_pref']
    format = workbook.add_format({'num_format': '0.00%'})
    worksheet.set_column(len(multiples_pref_global)+(not participating_global)*len(multiples_pref_global) + 5, len(multiples_pref_global)+(not participating_global)*len(multiples_pref_global) + 5, None, format)
    xlwriter.save()
    xlwriter.close()
    excel_file.seek(0)
    response = HttpResponse(excel_file.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=liquid_pref.xlsx'
    return response

def download_data_table(request):
    excel_file = IO()
    xlwriter = pd.ExcelWriter(excel_file, engine='xlsxwriter')
    data_table_global.to_excel(xlwriter, 'data_table')
    workbook  = xlwriter.book
    worksheet = xlwriter.sheets['data_table']
    #format = workbook.add_format({'num_format': '0.00%'})
    #worksheet.set_column(len(series_global)+2, len(series_global)+2, None, format)
    #worksheet.set_column(len(series_global+options_class_global)+4, len(series_global+options_class_global)+4, None, format)
    xlwriter.save()
    xlwriter.close()
    excel_file.seek(0)
    response = HttpResponse(excel_file.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=data_table.xlsx'
    return response