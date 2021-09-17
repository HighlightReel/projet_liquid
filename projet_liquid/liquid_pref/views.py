from . import computations
from django.shortcuts import render
from django.http import HttpResponse
import json

def post_traitement(request):
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
    
    return (investors, series, shares, options_holders, options_class, options)

# Create your views here.
def index(request):
    if request.method == "POST":
        investors, series, shares, options_holders, options_class, options = post_traitement(request)
        cap_table, cap_table_styled = computations.cap_table_function(investors, series, shares, options_holders, options_class, options)
        print(cap_table)
    return render(request, "liquid_pref/index.html")


