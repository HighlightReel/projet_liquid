from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("generate", views.generate, name="generate"),
    path("display", views.display, name="display"),
    path("download_cap_table", views.download_cap_table, name="download_cap_table"),
    path("download_liquid_pref", views.download_liquid_pref, name="download_liquid_pref"),
    path("plot", views.plot_graph, name="plot"),
    path("plot_parameters", views.plot_parameters, name="plot_parameters"),
    path("data_table", views.data_table, name="data_table"),
    path("download_data_table", views.download_data_table, name="download_data_table")
]
