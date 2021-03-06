import plotly as py
import plotly.graph_objs as go
import plotly.tools as tls
import csv
import os
from datetime import datetime
import statistics
import shutil
import markdown2
import pdfkit


class Spending:
    def __init__(self, row):
        self.date = datetime.strptime(row[0], "%d %b %Y ")
        self.reference = row[1]
        try:
            self.paidIn = float(row[3])
            self.paidOut = 0.0
            self.type = "PAID"
        except:
            self.paidOut = float(row[2])
            self.paidIn = 0.0
            self.type = "COST"
        self.balance = float(row[6])


class Account:
    def __init__(self, spend):
        if spend is not None:
            self.balance = spend.paidOut
            self.paying = spend.paidIn
            self.reference = spend.reference
            self.nb_visit = 1

    def add(self, spend):
        self.balance += spend.paidOut
        self.paying += spend.paidIn
        self.nb_visit += 1

    def tostring(self):
        if self.balance == 0.0:
            return str(self.reference) + ": You received " + str(round(self.paying, 1)) + "€ and visited it " \
                   + str(round(self.nb_visit, 1)) + " times."
        elif self.paying == 0.0:
            return str(self.reference) + ": You paid " + str(round(self.balance, 1)) + "€ and visited it " \
                   + str(round(self.nb_visit, 1)) + " times."


def createfolder(item):
    folder = item[:len(item) - 4]
    if os.path.exists(folder):
        shutil.rmtree(folder)
    os.mkdir(folder)
    shutil.copyfile(item, "./" + folder + "/" + item)
    shutil.copyfile("modest.css", "./" + folder + "/modest.css")
    os.chdir('./' + folder)


def get_name_report():
    folder = os.path.relpath(".", "..")
    return folder + ".md"


def get_name_report_html():
    folder = os.path.relpath(".", "..")
    return folder + ".html"


def get_name_report_pdf():
    folder = os.path.relpath(".", "..")
    return folder + ".pdf"


def append_step_for_all_year(i, step, tab_date, tab_money, tab_var, spending):
    if step == 1:
        tab_date.append(spending.date)
        if not tab_money:
            previous_val = 0
        else:
            previous_val = tab_money.pop()

        tab_var.append(previous_val - spending.balance)
        tab_money.append(previous_val)
        tab_money.append(spending.balance)
    elif i % step:
        tab_date.append(spending.date)
        if not tab_money:
            previous_val = 0
        else:
            previous_val = tab_money.pop()

        tab_var.append(previous_val - spending.balance)
        tab_money.append(previous_val)
        tab_money.append(spending.balance)


def plot_all_year(tab_spend):
    tab_date = []
    tab_money_day = []
    tab_variation_day = []

    tab_date_weekly = []
    tab_date_monthly = []
    tab_money_week = []
    tab_variation_weekly = []
    tab_money_month = []
    tab_variation_monthly = []

    tab_money_by_weekday = [0, 0, 0, 0, 0, 0, 0]
    tab_nb_visit_by_weekday = [0, 0, 0, 0, 0, 0, 0]
    tab_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    week = 7
    month = 30
    i = 1
    for spending in tab_spend:
        weekday = spending.date.weekday()
        tab_money_by_weekday[weekday] += spending.paidOut
        tab_nb_visit_by_weekday[weekday] += 1

        append_step_for_all_year(i, week, tab_date_weekly, tab_money_week, tab_variation_weekly, spending)

        append_step_for_all_year(i, month, tab_date_monthly, tab_money_month, tab_variation_monthly, spending)

        append_step_for_all_year(i, 1, tab_date, tab_money_day, tab_variation_day, spending)

        i += 1

    f = open(get_name_report(), "a", encoding="utf-8")
    f.write("\n\n## Plot of the whole csv file " + os.path.relpath(".", ".."))
    print("*** Writing plots for all time ***")

    f.write("\n\n### Pie charts\n")
    f.write("\n- [Pie Chart on money paid by merchant](./all_time/pie_char_balance_all_times.html)")
    f.write("\n- [Pie Chart on number of visits by merchant](./all_time/pie_char_visit_all_times.html)")
    f.write("\n- [Pie Chart on money spend by day of week](./all_time/pie_char_money_by_day_of_week_all_times.html)")
    f.write("\n- [Pie Chart on number of visit by day of week](./all_time/pie_char_visit_by_dayofweek_all_times.html)")

    draw_pie_of_week(tab_name, tab_money_by_weekday, "pie_char_money_by_day_of_week_all_times.html")
    draw_pie_of_week(tab_name, tab_nb_visit_by_weekday, "pie_char_visit_by_dayofweek_all_times.html")

    f.write("\n\n### Scatter plots\n")
    draw_scatter_plot("All time by day", tab_date, tab_money_day, tab_variation_day, "all_time", f)
    draw_scatter_plot("All time by week", tab_date_weekly, tab_money_week, tab_variation_weekly, "all_time", f)
    draw_scatter_plot("All time by month", tab_date_monthly, tab_money_month, tab_variation_monthly, "all_time", f)
    f.close()


def make_stats(filename):
    createfolder(filename)

    f = open(get_name_report(), "w", encoding="utf-8")
    f.write("## Report for the file " + os.path.relpath(".", ".."))
    f.close()
    print("*** Parsing file", filename, "***")
    tab_Spending = []
    csv_parser(tab_Spending, filename)

    print("*** Gathering Data ***")
    tab_money = []
    tab_name = []
    tab_visit = []

    dict_buy = gather_account(tab_Spending)

    for key, account in dict_buy.items():
        tab_money.append(account.balance)
        tab_name.append(str(key))
        tab_visit.append(account.nb_visit)

    draw_pie_charts(tab_name, tab_money, tab_visit)

    tab_year = []
    dict_Spending = dict()
    for ss in tab_Spending:
        year = ss.date.year
        if year not in tab_year:
            tab_year.append(year)
            dict_Spending.update({year: []})
        dict_Spending[year].append(ss)

    plot_all_year(tab_Spending)

    for year, spending in dict_Spending.items():
        print("*** Building plots for", year, "***")
        str_year = str(year)
        f = open(get_name_report(), "a")
        f.write("\n\n### Plot for the year " + str_year + "\n")
        f.close()

        if os.path.exists(str_year):
            shutil.rmtree(str_year)
        os.mkdir(str_year)
        plot_year(spending, str_year)

    html = open(get_name_report_html(), "w",  encoding="utf-8")
    html.write("<!DOCTYPE html>\n<html lang=\"en\">\n<head>"
               + "\n<title>Report " + get_name_report_html() + "</title>"
               + "<link rel=\"stylesheet\" href=\"modest.css\">"
               + "\n<meta charset=\"UTF-8\"></head>\n</body>\n")

    html.write(markdown2.markdown_path(get_name_report(), encoding="utf-8"))
    html.write("\n</body>\n</html>")
    html.close()

    path_wkthmltopdf = r'C:\_Installs\wkhtmltopdf\bin\wkhtmltopdf.exe'
    config = pdfkit.configuration(wkhtmltopdf=path_wkthmltopdf)
    pdfkit.from_file(get_name_report_html(), get_name_report_pdf(), configuration=config)


def csv_parser(spendings, filename):
    with open(filename, 'r', encoding="utf8") as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='|')
        iterrow = iter(reader)
        next(iterrow)
        for row in iterrow:
            spendings.append(Spending(row))


def sortmerchant(dict):
    sorted_balance = sorted(dict.items(), key=lambda x: x[1].balance, reverse=True)
    sorted_visite = sorted(dict.items(), key=lambda x: x[1].nb_visit, reverse=True)

    sorted_merchant_balance_obj = []
    sorted_merchant_visite_obj = []

    for tuplet in sorted_balance:
        strtuple = tuplet[0]
        sorted_merchant_balance_obj.append(dict[strtuple])

    for tuplet in sorted_visite:
        strtuple = tuplet[0]
        sorted_merchant_visite_obj.append(dict[strtuple])

    return [sorted_merchant_balance_obj, sorted_merchant_visite_obj]


def print10(tab, first=True):
    if not first:
        for i in range(len(tab) - 1, len(tab) - 11, -1):
            print(tab[i].tostring())
    else:
        for i in range(10):
            print(tab[i].tostring())


def print10_report(tab, file, first=True):
    k = 1
    if not first:
        for i in range(len(tab) - 1, len(tab) - 11, -1):
            file.write("\n" + str(k) + ". " + str(tab[i].tostring()))
            k += 1
    else:
        for i in range(10):
            file.write("\n" + str(k) + ". " + str(tab[i].tostring()))
            k += 1


def print_info_list_report(list, file):
    file.write("\n- The maximum spending : " + str(max(list)) + "€")
    file.write("\n- The minimum spending : " + str(min(list)) + "€")
    file.write("\n- The mean : " + str(round(statistics.mean(list), 1)) + "€")
    file.write("\n- The median : " + str(round(statistics.median(list), 1)) + "€")
    file.write("\n- The low mean : " + str(round(statistics.median_low(list), 1)) + "€")
    file.write("\n- The higher median : " + str(round(statistics.median_high(list), 1)) + "€")
    file.write("\n- The mode is " + str(round(statistics.mode(list), 1)) + "€")
    file.write("\n- The standard deviation is " + str(round(statistics.stdev(list), 1)) + "€")
    file.write("\n- The variance is " + str(round(statistics.variance(list), 1)) + "€")


def print_info_report(tab, tab_all_money):
    f = open(get_name_report(), "a", encoding="utf-8")

    f.write("\n\n### Info exchange ")
    f.write("\n\n#### Where you pay the most ? ")
    print10_report(tab[0], f)

    f.write("\n\n#### Where you pay the less ? ")
    print10_report(tab[0], f, False)

    f.write("\n\n#### Where you visit the most ? ")
    print10_report(tab[1], f)

    f.write("\n\n#### Where you visit the less ? ")
    print10_report(tab[1], f, False)

    f.write("\n\n#### Info about current money on account ")
    print_info_list_report(tab_all_money, f)

    f.close()


def printInfos(dict, tab_all_money):
    print("\n*** Info exchange ***")
    tab = sortmerchant(dict)

    print("*** Where you pay the most ? ***")
    print10(tab[0])

    print("\n*** Where you pay the less ? ***")
    print10(tab[0], False)

    print("\n*** Where you visit the most ? ***")
    print10(tab[1])

    print("\n*** Where you visit the less ? ***")
    print10(tab[1], False)
    print("\n*** Info about current money on account ***")
    printInfoList(tab_all_money)

    print_info_report(tab, tab_all_money)


def init_tab(nb, axis, balance, spending):
    for i in range(nb):
        axis.append(i)
        balance.append(0)
        spending.append(0)


def gather_account(tab_tab):
    tab_all_money = []
    dict_buy = dict()

    for spending in tab_tab:
        tab_all_money.append(spending.balance)
        merchant = str(spending.reference)

        if merchant not in dict_buy:
            dict_buy.update({merchant: Account(spending)})
        else:
            merc = dict_buy[merchant]
            merc.add(spending)
            dict_buy.update({merchant: merc})

    printInfos(dict_buy, tab_all_money)

    return dict_buy


def draw_pie_of_week(tab_name, tab_money, filename):
    print("*** Draw Pie charts ***")

    fig = {
        'data': [{'labels': tab_name,
                  'values': tab_money,
                  'rotation': 235,
                  'type': 'pie'}],
        'layout': {'title': 'Money spend by day of week'}
    }

    py.offline.plot(fig, validate=True, auto_open=False, filename=filename, image_width=800, image_height=800)
    os.rename(filename, "all_time/" + filename)


def draw_pie_charts(tab_name, tab_money, tab_visit):
    print("*** Draw Pie charts ***")

    if os.path.exists("all_time"):
        shutil.rmtree("all_time")
    os.mkdir("all_time")

    fig = {
        'data': [{'labels': tab_name,
                  'values': tab_money,
                  'rotation': 235,
                  'type': 'pie'}],
        'layout': {'title': 'Money paid by merchant'}
    }
    filename = "pie_char_balance_all_times.html"

    py.offline.plot(fig, validate=True, auto_open=False, filename=filename, image_width=800, image_height=800)

    os.rename(filename, "all_time/" + filename)

    fig = {
        'data': [{'labels': tab_name,
                  'values': tab_visit,
                  'type': 'pie'}],
        'layout': {'title': 'Number of visits by merchant'}
    }

    filename = "pie_char_visit_all_times.html"
    py.offline.plot(fig, validate=True, auto_open=False, filename=filename, image_width=800, image_height=800)

    os.rename(filename, "all_time/" + filename)


def printInfoExchage(obj):
    print("Your most expensive merchant is ", obj[0][0], " with ", obj[0][1], "€ spend and visited ", obj[0][2],
          " times.")
    print("The less expensive merchant is ", obj[1][0], " with only ", obj[1][1], "€ spend and visited ", obj[1][2],
          " times.")
    print("Your most visited merchant is ", obj[2][0], " with ", obj[2][1], "€ spend and visited ", obj[2][2],
          " times.")
    print("The less visited merchant is ", obj[3][0], " with only ", obj[3][1], "€ spend and visited ", obj[3][2],
          " times.")


def printInfoList(list):
    print("\nThe maximum spending : ", max(list), "€")
    print("The minimum spending : ", min(list), "€")
    print("The mean : ", round(statistics.mean(list), 1), "€")
    print("The median : ", round(statistics.median(list), 1), "€")
    print("The low mean : ", round(statistics.median_low(list), 1), "€")
    print("The higher median : ", round(statistics.median_high(list), 1), "€")
    print("The mode is ", round(statistics.mode(list), 1), "€")
    print("The standard deviation is ", round(statistics.stdev(list), 1), "€")
    print("The variance is ", round(statistics.variance(list), 1), "€")


def barplot(tab1, tab2, title, name):
    data = [go.Bar(x=tab1, y=tab2)]
    label = [dict(x=xi, y=yi,
                  text=str(round(yi, 1)),
                  xanchor='center',
                  yanchor='bottom',
                  showarrow=False,
                  ) for xi, yi in zip(tab1, tab2)]
    py.offline.plot(data, validate=True, auto_open=False, filename=name, image_width=800, image_height=600)
    # help(py.offline.plot)


def scatterplot(tab1, tab2, title, name):
    layout = go.Layout(
        title=title,
        hovermode='closest',
        xaxis=dict(
            autorange=True,
            title='Time',
            ticklen=5,
            zeroline=True,
            showline=True,
            autotick=True,
            ticks='',
            gridwidth=2
        ),
        yaxis=dict(
            autorange=True,
            title='Money',
            ticklen=5,
            zeroline=True,
            showline=True,
            autotick=True,
            ticks='',
            gridwidth=2

        ),
        showlegend=False
    )
    fig = {
        'data': [go.Scatter(x=tab1, y=tab2)],
        'layout': layout
    }

    py.offline.plot(fig, validate=True, auto_open=False, filename=name, image_width=800, image_height=600)


def plot_year(tab_spending, year=None):
    tab_month_name = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    tab_date = []
    tab_money_day = []
    tab_variation_day = []

    tab_date_weekly = []
    tab_money_week = []
    tab_variation_weekly = []
    tab_money_month = []
    tab_variation_monthly = []

    week = 7
    month = 30
    i = 1
    for spending in tab_spending:
        append_step_for_all_year(i, week, tab_date_weekly, tab_money_week, tab_variation_weekly, spending)

        append_step_for_all_year(i, month, tab_month_name, tab_money_month, tab_variation_monthly, spending)

        append_step_for_all_year(i, 1, tab_date, tab_money_day, tab_variation_day, spending)

        i += 1

    f = open(get_name_report(), "a")

    draw_scatter_plot("Day", tab_date, tab_money_day, tab_variation_day, year, f)

    draw_bar_plot("Week", tab_date_weekly, tab_money_week, tab_variation_weekly, year, f)

    draw_scatter_plot("Week", tab_date_weekly, tab_money_week, tab_variation_weekly, year, f)

    draw_bar_plot("Month", tab_month_name, tab_money_month, tab_variation_monthly, year, f)

    f.close()


def draw_scatter_plot(time, tab1, tab2, tab3, year, f):
    f.write("\n#### Plots by " + time)
    print("*** Building plots by " + time + "***")
    filename = time + "_balance_scatter.html"
    title = "Balance by " + time

    scatterplot(tab1, tab2, 'balance by ' + time, filename)

    os.rename(filename, year + '/' + filename)
    f.write("\n- [" + title + "](./" + year + '/' + filename + ')')
    filename = time + '_variation_scatter.html'
    title = 'Variation by ' + time
    scatterplot(tab1, tab3, title, filename)

    os.rename(filename, year + '/' + filename)
    f.write("\n- [" + title + "](./" + year + '/' + filename + ')')


def draw_bar_plot(time, tab1, tab2, tab3, year, f):
    f.write("\n#### Plots by " + time)
    print("*** Building plots by " + time + "***")
    filename = time + '_balance_bar.html'
    title = 'Balance by ' + time
    barplot(tab1, tab2, 'Balance by ' + time, filename)

    os.rename(filename, year + '/' + filename)
    f.write("\n- [" + title + "](./" + year + '/' + filename + ')')
    filename = time + '_variation_bar.html'
    title = 'Variation by ' + time
    barplot(tab1, tab3, title, filename)

    os.rename(filename, year + '/' + filename)
    f.write("\n- [" + title + "](./" + year + '/' + filename + ')')
