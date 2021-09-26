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
    sale_price = forms.FloatField(label="Equity value (€)", initial=100000000, widget=forms.NumberInput(attrs={'style': 'width:150px'}))
    multiples_pref = SimpleArrayField(forms.CharField(max_length=100), initial=[1,1,1], widget=forms.TextInput(attrs={'style': 'width:80px'}))

class NewFormPlot(forms.Form):
    floor = forms.IntegerField(label="Minimum", initial=10000000, widget=forms.NumberInput(attrs={'style': 'width:150px'}))
    ceiling = forms.IntegerField(label="Maximum", initial=100000000, widget=forms.NumberInput(attrs={'style': 'width:150px'}))
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
    if request.method == "GET":
        request.session['investors_global'] = []
        request.session['series_global'] = []
        request.session['shares_global'] = []
        request.session['options_holders_global'] = []
        request.session['options_class_global'] = []
        request.session['options_global'] = []
        request.session['cap_table_global'] = []
        request.session['liquid_pref_global'] = []
        request.session['shares_prices_global'] = []
        request.session['options_prices_global'] = []

        request.session['first_step_global'] = "Nominal"
        request.session['carve_out_rate_global'] = 20
        request.session['participating_global'] = True
        request.session['sale_price_global'] = 100000000
        request.session['multiples_pref_global'] = [1,1,1]

        request.session['floor_global'] = 10000000
        request.session['ceiling_global'] = 200000000
        request.session['step_global'] = 1000000
        request.session['data_table_global'] = []

    if request.method == "POST":
        investors, series, shares, options_holders, options_class, options, shares_prices, options_prices = cap_table_post_traitement(request)
        cap_table, cap_table_styled = computations.cap_table_function(investors, series, shares, options_holders, options_class, options)

        request.session['investors_global'] = investors
        request.session['series_global'] = series 
        request.session['shares_global'] = shares
        request.session['options_holders_global'] = options_holders
        request.session['options_class_global'] = options_class
        request.session['options_global'] = options
        request.session['cap_table_global'] = cap_table.to_json()
        request.session['shares_prices_global'] = list(map(float,shares_prices))
        request.session['options_prices_global'] = list(map(float,options_prices))

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

            request.session['first_step_global'] = first_step
            request.session['carve_out_rate_global'] = carve_out_rate
            request.session['participating_global'] = participating
            request.session['sale_price_global'] = sale_price
            request.session['multiples_pref_global'] = multiples_pref

            message="Saved"
        
        return HttpResponse(json.dumps(message))

def plot_parameters(request):
    if request.method == "POST":
        form = NewFormPlot(request.POST)
        if form.is_valid():
            floor = form.cleaned_data["floor"]
            ceiling = form.cleaned_data["ceiling"]
            step = form.cleaned_data["step"]

            request.session['floor_global'] = floor
            request.session['ceiling_global']  = ceiling
            request.session['step_global']  = step

            message="Saved"

        return HttpResponse(json.dumps(message))


def display(request):
    liquid_pref, liquid_pref_styled, iteration = computations.liquid_pref_function(pd.read_json(request.session['cap_table_global']), request.session['series_global'], request.session['investors_global'], request.session['options_holders_global'], request.session['options_class_global'], request.session['first_step_global'], request.session['carve_out_rate_global'], request.session['multiples_pref_global'], request.session['participating_global'], request.session['shares_prices_global'], request.session['sale_price_global'], request.session['options_prices_global'], request.session['options_global'], 0, request.session['shares_global'])
    request.session['liquid_pref_global'] = liquid_pref.to_json()
    return JsonResponse({"liquid_pref": liquid_pref_styled.render().replace("<table ", "<table class='table table-hover table-striped' "), "iteration": iteration})

def plot_graph(request):
    plot_div = computations.plot_liquid_pref(pd.read_json(request.session['cap_table_global']), request.session['series_global'], request.session['investors_global'], request.session['options_holders_global'], request.session['options_class_global'], request.session['first_step_global'], request.session['carve_out_rate_global'], request.session['multiples_pref_global'], request.session['participating_global'], request.session['shares_prices_global'], request.session['options_prices_global'], request.session['options_global'], request.session['floor_global'], request.session['ceiling_global'], request.session['step_global'], request.session['shares_global'])
    return JsonResponse(plot_div, safe=False)

def data_table(request):
    df, df_styled = computations.compute_data_table(pd.read_json(request.session['cap_table_global']), request.session['series_global'], request.session['investors_global'], request.session['options_holders_global'], request.session['options_class_global'], request.session['first_step_global'], request.session['carve_out_rate_global'], request.session['multiples_pref_global'], request.session['participating_global'], request.session['shares_prices_global'], request.session['options_prices_global'], request.session['options_global'], request.session['floor_global'], request.session['ceiling_global'], request.session['step_global'], request.session['shares_global'])
    request.session['data_table_global'] = df.to_json()
    return HttpResponse(df_styled.render().replace("<table ", "<table class='table table-hover table-striped' "))

def download_cap_table(request):
    excel_file = IO()
    xlwriter = pd.ExcelWriter(excel_file, engine='xlsxwriter')
    pd.read_json(request.session['cap_table_global']).to_excel(xlwriter, 'cap_table')
    workbook  = xlwriter.book
    worksheet = xlwriter.sheets['cap_table']
    format = workbook.add_format({'num_format': '0.00%'})
    worksheet.set_column(len(request.session['series_global'])+2, len(request.session['series_global'])+2, None, format)
    worksheet.set_column(len(request.session['series_global']+request.session['options_class_global'])+4, len(request.session['series_global']+request.session['options_class_global'])+4, None, format)
    xlwriter.save()
    xlwriter.close()
    excel_file.seek(0)
    response = HttpResponse(excel_file.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=cap_table.xlsx'
    return response

def download_liquid_pref(request):
    excel_file = IO()
    xlwriter = pd.ExcelWriter(excel_file, engine='xlsxwriter')
    pd.read_json(request.session['liquid_pref_global']).to_excel(xlwriter, 'liquid_pref')
    workbook  = xlwriter.book
    worksheet = xlwriter.sheets['liquid_pref']
    format = workbook.add_format({'num_format': '0.00%'})
    worksheet.set_column(len(request.session['multiples_pref_global'])+(not request.session['participating_global'])*len(request.session['multiples_pref_global']) + 5, len(request.session['multiples_pref_global'])+(not request.session['participating_global'])*len(request.session['multiples_pref_global']) + 5, None, format)
    xlwriter.save()
    xlwriter.close()
    excel_file.seek(0)
    response = HttpResponse(excel_file.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=liquid_pref.xlsx'
    return response

def download_data_table(request):
    excel_file = IO()
    xlwriter = pd.ExcelWriter(excel_file, engine='xlsxwriter')
    pd.read_json(request.session['data_table_global']).to_excel(xlwriter, 'data_table')
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