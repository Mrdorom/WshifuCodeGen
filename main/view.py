from django.shortcuts import render_to_response, render

index_html = render_to_response('index.html')


def index(request):
    return index_html
    # return render_to_response('index.html')


def gen(request):
    d = {}
    # try
    #
    # except:
    #     return render(request, "post.html", d)
