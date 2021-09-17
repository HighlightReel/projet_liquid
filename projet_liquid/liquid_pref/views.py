from django import http
from django.http.response import JsonResponse
from . import computations
from django.shortcuts import render
from django.http import HttpResponse
import json
from django import forms
from django.contrib.postgres.forms import SimpleArrayField
import distutils
from distutils import util



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

first_step_global = []
Galion_rate_global = []
participating_global = []
sale_price_global = []
multiples_pref_global = []

class NewForm(forms.Form):
    first_step = forms.MultipleChoiceField(choices = (
    ("Nominal", "Nominal"),
    ("Galion", "Galion"),
    ))
    Galion_rate = forms.IntegerField(label="Galion rate")
    participating = forms.MultipleChoiceField(choices = (
    (True, "Yes"),
    (False, "No"),
    ))
    sale_price = forms.FloatField(label="Sale price")
    multiples_pref = SimpleArrayField(forms.CharField(max_length=100), initial=[1,1,1,1])


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


def liquid_pref_post_traitement(request):

    cap_table = cap_table_global 
    series = series_global
    investors = investors_global
    options_holders = options_holders_global
    options_class = options_class_global

    #first_step = "Nominal" # equal Nominal or Galion
    #Galion_rate = 20
    #multiples_pref = [1,1,1]
    #participating = True
    #shares_prices = [0.1,38,45,67.5]
    #options_prices = [45, 67.5]
    #sale_price = 100000000
    
    return (cap_table, series, investors, options_holders, options_class, first_step, Galion_rate, multiples_pref, participating, shares_prices, sale_price)

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
        shares_prices_global = shares_prices
        options_prices_global = options_prices
        
        return HttpResponse(cap_table.to_html(classes='table table-striped'))
    return render(request, "liquid_pref/index.html", {
        "form": NewForm()
    })

def generate(request):
    if request.method == "POST":
        form = NewForm(request.POST)
        if form.is_valid():
            first_step = form.cleaned_data["first_step"]
            Galion_rate = form.cleaned_data["Galion_rate"]
            participating = bool(distutils.util.strtobool(form.cleaned_data["participating"][0]))
            sale_price = form.cleaned_data["sale_price"]
            multiples_pref = form.cleaned_data["multiples_pref"]
            if (participating):
                print("Yes là")
        #cap_table, series, investors, options_holders, options_class, first_step, Galion_rate, multiples_pref, participating, shares_prices, sale_price = liquid_pref_post_traitement(request)
        #liquid_pref, liquid_pref_styled = computations.liquid_pref_function(cap_table, series, investors, options_holders, options_class, first_step, Galion_rate, multiples_pref, participating, shares_prices, sale_price)
        return render(request, "liquid_pref/index.html", {
        "form": form
        })
        #return HttpResponse(liquid_pref.to_html(classes='table table-striped'))

def display(request):
    
    #il faut return du JSON
    
    return HttpResponse("Ca marche")
    #return HttpResponse(liquid_pref_global.to_html(classes='table table-striped'))