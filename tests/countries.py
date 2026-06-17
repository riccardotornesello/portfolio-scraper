from portfolio_scraper.utils.country import get_language_map

if __name__ == "__main__":
    countries = get_language_map("ita")
    print(countries["NORVEGIA"])
    print(countries["CANADA"])
