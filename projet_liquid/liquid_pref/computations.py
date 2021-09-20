import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from plotly.offline import plot
import plotly.graph_objects as go
import plotly
import json

def cap_table_function(investors, series, shares, options_holders, options_class, options):
    
    #cap table init
    shares_data = []
    options_data = []
    
    for i in range (len(investors)):
        add = shares[i] + len(options_class)*[0]
        shares_data.append(add)
    
    for i in range (len(options_holders)):
        add = len(series)*[0] + options[i]
        options_data.append(add)
        
    data = shares_data + options_data
    index_list = investors + options_holders
    columns_list = series + options_class
    
    cap_table = pd.DataFrame(data, index = index_list, columns = columns_list)
    
    #Add columns total NFD and FD
    cap_table.insert(len(series), "Total NFD", cap_table[series].sum(axis=1))
    cap_table.insert(len(columns_list)+1, "Total FD", cap_table[columns_list].sum(axis=1))
    columns_list.append("Total NFD")
    columns_list.append("Total FD")
    
    #Columns total
    for i in range (len(columns_list)):
        cap_table.loc["Total", columns_list[i]] = cap_table[columns_list[i]].sum()
        
    #% column
    cap_table.insert(len(series)+1, "Total NFD (%)", cap_table["Total NFD"] / cap_table.at["Total", "Total NFD"])
    cap_table.insert(len(columns_list)+1, "Total FD (%)", cap_table["Total FD"] / cap_table.at["Total", "Total FD"])
        
    #format
    format_dict = { i : '{:,.0f}'.format for i in list(cap_table.columns) }
    format_dict["Total NFD (%)"] = '{:,.2%}'.format
    format_dict["Total FD (%)"] = '{:,.2%}'.format

    return (cap_table, cap_table.style.format(format_dict))


def liquid_pref_function(cap_table, series, investors, options_holders, options_class, first_step, carve_out_rate, multiples_pref, participating, shares_prices, sale_price):
    
    first_step_item = first_step + (first_step == "Carve-out")*(": " + str(carve_out_rate) + "%")
        
    liquid_pref_steps = [first_step_item]
    for i in range (len(series)-1):
        add = series[-1-i].split(' ')[0]
        liquid_pref_steps.append(f"Pref: {add}")
    liquid_pref_steps.append("Prorata")
    liquid_pref_steps
    
    index_list = investors + options_holders

    #liquid pref init
    liquid_pref = pd.DataFrame(index = index_list+["Total"], columns = liquid_pref_steps)
    solde = []
    price_step_list = []


    #First step
    if (first_step == "Nominal"):
        price_step = shares_prices[0]
        price_step_list.append(price_step)
        liquid_pref[liquid_pref_steps[0]] = cap_table["Total FD"] * price_step
    elif (first_step == "Carve-out"):
        price_step = carve_out_rate/100 * sale_price / cap_table.at["Total", "Total FD"]
        price_step_list.append(price_step)
        liquid_pref[liquid_pref_steps[0]] = cap_table["Total FD"] * price_step
    else:
        print("ERROR FIRST STEP")
    solde.append(sale_price - liquid_pref.at["Total", liquid_pref_steps[0]])


    #Pref
    for i in range (len(liquid_pref_steps)-2):
        price_step = max(0, multiples_pref[i]*shares_prices[-1-i]-price_step_list[0])
        price_step_list.append(price_step)
        if (solde[-1] >= (cap_table.at["Total", series[-1-i]] * price_step)):
            liquid_pref[liquid_pref_steps[i+1]] = cap_table[series[-1-i]] * price_step
        else:
            liquid_pref[liquid_pref_steps[i+1]] = cap_table[series[-1-i]] * solde[-1] / cap_table.at["Total", series[-1-i]]
        solde.append(solde[-1] - liquid_pref.at["Total", liquid_pref_steps[i+1]])

    #prorata
    if (participating):
        price_step = solde[-1] / cap_table.at["Total", "Total FD"]
        price_step_list.append(price_step)
        liquid_pref[liquid_pref_steps[-1]] = cap_table["Total FD (%)"] * solde[-1]
        solde.append(solde[-1] - liquid_pref.at["Total", liquid_pref_steps[-1]])
    else:
        initial_liquid_pref_steps_len = len(liquid_pref_steps)
        initial_price_step_list = price_step_list.copy()
        #catchup
        for i in range (initial_liquid_pref_steps_len-2):
            price_step = initial_price_step_list[-1-i] - (i != 0)*initial_price_step_list[-i]
            price_step_list.append(price_step)
            new_column_value = (cap_table.iloc[:, 0:i+1].sum(axis=1)+cap_table.iloc[:, (len(series)+2):(len(series)+2+len(options_class))].sum(axis=1))
            total = (new_column_value*price_step)["Total"] 
            if (solde[-1] >= total):
                liquid_pref.insert(initial_liquid_pref_steps_len-1+i, f"Catchup {i+1}", new_column_value*price_step)
            else:
                liquid_pref.insert(initial_liquid_pref_steps_len-1+i, f"Catchup {i+1}", new_column_value * solde[-1] / new_column_value["Total"])
            liquid_pref_steps.insert(initial_liquid_pref_steps_len-1+i, f"Catchup {i+1}")
            solde.append(solde[-1] - liquid_pref.at["Total", f"Catchup {i+1}"])
        #prorata
        price_step = solde[-1] / cap_table.at["Total", "Total FD"]
        price_step_list.append(price_step)
        liquid_pref[liquid_pref_steps[-1]] = cap_table["Total FD (%)"] * solde[-1]
        solde.append(solde[-1] - liquid_pref.at["Total", liquid_pref_steps[-1]])

    #Lines total
    for i in range (len(index_list)):
        liquid_pref.loc[index_list[i], "Total proceeds"] = liquid_pref.loc[index_list[i],].sum()

    #Grand total
    liquid_pref.loc["Total","Total proceeds"] = liquid_pref.loc["Total",].sum()

    #solde + price_step
    for i in range (len(liquid_pref_steps)):
        liquid_pref.loc["Solde", liquid_pref_steps[i]] = solde[i]
        liquid_pref.loc["Prix", liquid_pref_steps[i]] = price_step_list[i] 


    # vs prorata / delta
    for i in range (len(index_list)):
        liquid_pref.loc[index_list[i], "vs prorata"] = cap_table.at[index_list[i], "Total FD (%)"] * sale_price
        liquid_pref.loc[index_list[i], "% delta"] = liquid_pref.at[index_list[i], "Total proceeds"] / liquid_pref.at[index_list[i], "vs prorata"] - 1
    liquid_pref.loc["Total", "vs prorata"] = cap_table.at["Total", "Total FD (%)"] * sale_price
    liquid_pref.loc["Total", "% delta"] = liquid_pref.at["Total", "Total proceeds"] / liquid_pref.at["Total", "vs prorata"] - 1


    #format
    format_dict = { i : '{:,.2f} €'.format for i in list(liquid_pref.columns)}
    format_dict["% delta"] = '{:,.2%}'.format
    liquid_pref.style.format(format_dict)

    return (liquid_pref, liquid_pref.style.format(format_dict))

def plot_liquid_pref(cap_table, series, investors, options_holders, options_class, first_step, carve_out_rate, multiples_pref, participating, shares_prices, floor, ceiling, step):
    graphe = []
    x = []
    for i in range(floor, ceiling+step, step):
        x.append(i)


    for sale_price in range (floor, ceiling+step, step):
        liquid_pref, liquid_pref_styled = liquid_pref_function(cap_table, series, investors, options_holders, options_class, first_step, carve_out_rate, multiples_pref, participating, shares_prices, sale_price)
        proceeds = []
        for investor in (investors+options_holders):
            proceeds.append(liquid_pref["Total proceeds"][investor])
        graphe.append(proceeds)

    fig = go.Figure()
    for i in range (len(investors+options_holders)):
        fig.add_trace(go.Scatter(x=x, y=[item[i] for item in graphe],
                        mode='lines',
                        name=(investors+options_holders)[i]))

    fig.update_layout(title='<b>Liquid pref simulation</b>', title_x=0.5,
                    xaxis_title='Sale price (€)',
                    yaxis_title='Proceeds (€)')

    liquidGraph = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return(liquidGraph)

def compute_data_table(cap_table, series, investors, options_holders, options_class, first_step, carve_out_rate, multiples_pref, participating, shares_prices, floor, ceiling, step):
    graphe = []

    for sale_price in range (floor, ceiling+step, step):
        liquid_pref, liquid_pref_styled = liquid_pref_function(cap_table, series, investors, options_holders, options_class, first_step, carve_out_rate, multiples_pref, participating, shares_prices, sale_price)
        proceeds = []
        for investor in (investors+options_holders+["Total"]):
            proceeds.append(liquid_pref["Total proceeds"][investor])
        graphe.append(proceeds)

    df = pd.DataFrame(np.array(graphe).T.tolist(), columns=list(range(floor, ceiling+step, step)), index=investors+options_holders+["Total"])

    #format
    df.columns = list(df.columns.map(str))
    df.columns = list(map(int, df.columns))
    df.columns = [f'{cur:,} €' for cur in df.columns]
    format_dict = { i : '{:,.2f} €'.format for i in list(df.columns)}
    
    return(df, df.style.format(format_dict))