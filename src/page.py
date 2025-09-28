URL_API = "https://zh.wikipedia.org/w/api.php"


def query_slang():
    params = {
        "action": "parse",
        "format": "json",
        "prop": "wikitext",
        "uselang": "zh",
        "formatversion": "2",
        "page": "中国大陆网络用语列表",
    }


def query_redirect():
    params = {
        "action": "query",
        "format": "json",
        "list": "categorymembers",
        "cmtitle": "Category:錯字重定向",
        "cmlimit": "max",
    }
