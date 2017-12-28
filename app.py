from flask import Flask, render_template, request, url_for

import taxdiff

app = Flask(__name__)

def zero(value):
  if request.args.get(value):
    return int(request.args.get(value))
  return 0

@app.route("/")
def hello():
  calculate = False
  diff = 0
  data1 = {}
  data2 = {}
  gain = False
  if request.args.get('calculate'):
    calculate = True
    data = {
      'wages': zero('wages'),
      'interest': zero('interest'),
      'dividends': zero('dividends'),
      'state_tax_refunds': zero('state_tax_refunds'),
      'short_term_gains': zero('short_term_gains'),
      'long_term_gains': zero('long_term_gains'),
      'hsa': zero('hsa'),
      'mortgage': zero('mortgage'),
      'state_taxes': zero('state_taxes')
    }
    data1 = taxdiff.compute(data, False)
    data2 = taxdiff.compute(data, True)
    diff = float(data2['total_taxes'].replace(',','')) - \
           float(data1['total_taxes'].replace(',',''))
    if diff == abs(diff):
      gain = False
    else:
      gain = True
    diff = "{:,}".format(abs(diff))
  return render_template('tax.html',
                         form_css = url_for('static', filename='form.css'),
                         wages = zero('wages'),
                         interest = zero('interest'),
                         dividends = zero('dividends'),
                         state_tax_refunds = zero('state_tax_refunds'),
                         short_term_gains = zero('short_term_gains'),
                         long_term_gains = zero('long_term_gains'),
                         hsa = zero('hsa'),
                         mortgage = zero('mortgage'),
                         state_taxes = zero('state_taxes'),
                         calculate = calculate,
                         taxdiff = diff,
                         gain = gain,
                         data1 = data1,
                         data2 = data2)