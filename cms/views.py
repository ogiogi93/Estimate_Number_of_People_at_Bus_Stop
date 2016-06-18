from django.shortcuts import render, render_to_response
from django.template import RequestContext
from cms.models import Result
import datetime
import pandas as pd


def top_page(request):
    data = Result.objects.filter(date__startswith=datetime.date(2016, 5, 31)).values()
    df_data = pd.DataFrame(list(data))
    return render_to_response('bus_line/index.html',
                              {'result': df_data.to_json(orient='records')},
                              context_instance=RequestContext(request))
