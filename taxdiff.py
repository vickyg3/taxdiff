#! /usr/bin/python

import sys

BRACKETS = [
  # (limit, tax factor, extra)
  (0, 0, 0),
  (18550, 0.1, 0),
  (75300, 0.15, 1855),
  (151900, 0.25, 10367.50),
  (231450, 0.28, 29517.50),
  (413350, 0.33, 51791.50),
  (466950, 0.35, 111818.50),
  (sys.maxint, 0.396, 130578.50)
]

NEW_BRACKETS = [
  # (limit, tax factor, extra)
  (0, 0, 0),
  (19050, 0.1, 0),
  (77400, 0.12, 1905),
  (165000, 0.22, 8907),
  (315000, 0.24, 28179),
  (400000, 0.32, 64179),
  (600000, 0.35, 91379),
  (sys.maxint, 0.37, 161379)
]

def schedule_a(data, agi, standard_deduction, salt_cap):
  itemized_deductions = min(data['state_taxes'], salt_cap) + data['mortgage']
  # see itemized deduction worksheet for this calculation:
  # https://www.irs.gov/pub/irs-pdf/i1040sca.pdf
  line6 = 311300
  if line6 > agi:
    return (max(itemized_deductions, standard_deduction), 0)
  line8 = int(round((agi - line6) * 0.03))
  line4 = int(round(itemized_deductions * 0.8))
  line9 = min(line4, line8)
  itemized_deductions -= line9
  return (max(itemized_deductions, standard_deduction), line9)

def tax(income, brackets):
  for i, bracket in enumerate(brackets):
    if income < bracket[0]:
      return int(round(bracket[2] + (bracket[1] * (income - brackets[i - 1][0]))))

def qual_div(data, taxable_income, brackets):
  # Qualified Dividends and Capital Gain Tax Worksheet
  # https://apps.irs.gov/app/vita/content/globalmedia/capital_gain_tax_worksheet_1040i.pdf
  line2 = 0 # qualified dividends
  long_term = data.get('long_term_gains', 0)
  total_gain = long_term + data.get('short_term_gains', 0)
  line3 = min(long_term, total_gain)
  line4 = line2 + line3
  line6 = line4
  line7 = taxable_income - line4
  line8 = 75300
  line9 = min(taxable_income, line8)
  line10 = min(line7, line9)
  line11 = line9 - line10
  line12 = min(taxable_income, line4)
  line14 = line12 - line11
  line16 = min(466950, taxable_income)
  line17 = line7 + line11
  line18 = max(line16 - line17, 0)
  line19 = min(line14, line18)
  line20 = int(round(line19 * 0.15))
  line21 = line11 + line19
  line22 = line12 - line21
  line23 = int(round(line22 * 0.2))
  line24 = tax(line7, brackets)
  line25 = line20 + line23 + line24
  line26 = tax(taxable_income, brackets)
  return (min(line25, line26), line6, line7)

def amt_bracket(income):
  if income <= 186300:
    return int(round(income * 0.26))
  else:
    return int(round(income * 0.28)) - 3726


def amt(new_tax_law, data, taxes, agi, taxable_income_before_exemptions, 
        line9_itemized_deduction, line6_qual_div, line7_qual_div):
  # https://www.irs.gov/pub/irs-pdf/i6251.pdf
  # assumes itemizing
  if agi < 311300:
    line6 = 0
  else:
    line6 = line9_itemized_deduction
  am_taxable_income = taxable_income_before_exemptions + data['state_taxes'] + \
                      - data['state_tax_refunds'] - line6
  if new_tax_law:
    exemption = 109400 # assumes no AMT phase out.
  elif am_taxable_income < 159700:
    exemption = 83800
  else:
    # exemption worksheet
    line4 = max(am_taxable_income - 159700, 0)
    line5 = int(round(line4 * 0.25))
    line6 = max(83800 - line5, 0)
    exemption = line6
  am_taxable_income_after_exemption = am_taxable_income - exemption
  if data.get('short_term_gains', 0) > 0 or data.get('long_term_gains', 0) > 0:
    # part iii
    line36 = am_taxable_income_after_exemption
    line37 = line6_qual_div
    # TODO: need to to schedule d tax worksheet to get the second value here.
    line39 = min(line37, sys.maxint)
    line40 = min(line36, line39)
    line41 = line36 - line40
    line42 = amt_bracket(line41)
    line43 = 75300
    line44 = line7_qual_div
    line45 = max(line43 - line44, 0)
    line46 = min(line36, line37)
    line47 = min(line45, line46)
    line48 = line46 - line47
    line49 = 466950
    line50 = line45
    line51 = line7_qual_div
    line52 = line50 + line51
    line53 = max(line49 - line52, 0)
    line54 = min(line48, line53)
    line55 = int(round(line54 * 0.15))
    line56 = line47 + line54
    line57 = line46 - line56
    line58 = int(round(line57 * 0.2))
    line62 = line42 + line55 + line58
    line63 = amt_bracket(line36)
    tentative_minimum_tax = min(line62, line63)
  else:
    tentative_minimum_tax = amt_bracket(am_taxable_income_after_exemption)
  return max(tentative_minimum_tax - taxes, 0)

def compute(data, new_tax_law):
  if not new_tax_law:
    total_income = data['wages'] + data['interest'] + data['dividends'] + \
                   data['state_tax_refunds'] + data['short_term_gains'] + \
                   data['long_term_gains']
    agi = total_income - (data['hsa'])
    deductions, line9_itemized_deduction = schedule_a(data, agi, 12600, sys.maxint)
    exemptions = 0 # TODO: calculate this properly
    taxable_income_before_exemptions = agi - deductions
    taxable_income = taxable_income_before_exemptions - exemptions
    line6_qual_div = 0
    line7_qual_div = 0
    # this only works if the net capital gain is positive.
    if data.get('short_term_gains', 0) != 0 or data.get('long_term_gains') != 0:
      taxes, line6_qual_div, line7_qual_div = qual_div(data, taxable_income, BRACKETS)
    else:
      taxes = tax(taxable_income, BRACKETS)
    alternative = amt(False, data, taxes, agi, taxable_income_before_exemptions, \
                      line9_itemized_deduction, line6_qual_div, line7_qual_div)
  else:
    total_income = data['wages'] + data['interest'] + data['dividends'] + \
                   data['state_tax_refunds'] + data['short_term_gains'] + \
                   data['long_term_gains']
    agi = total_income - (data['hsa'])
    deductions, line9_itemized_deduction = schedule_a(data, agi, 24000, 10000)
    exemptions = 0 # TODO: calculate this properly
    taxable_income_before_exemptions = agi - deductions
    taxable_income = taxable_income_before_exemptions - exemptions
    line6_qual_div = 0
    line7_qual_div = 0
    # this only works if the net capital gain is positive.
    if data.get('short_term_gains', 0) != 0 or data.get('long_term_gains') != 0:
      taxes, line6_qual_div, line7_qual_div = qual_div(data, taxable_income,
                                                       NEW_BRACKETS)
    else:
      taxes = tax(taxable_income, NEW_BRACKETS)
    alternative = amt(True, data, taxes, agi, taxable_income_before_exemptions, \
                      line9_itemized_deduction, line6_qual_div, line7_qual_div)
  total_taxes = taxes + alternative
  if total_income != 0:
    effective_rate = round((total_taxes * 1.0 / total_income) * 100, 2)
  else:
    effective_rate = 0
  ret = {
    'total_income': "{:,}".format(total_income),
    'agi': "{:,}".format(agi),
    'deductions': "{:,}".format(deductions),
    'taxable_income': "{:,}".format(taxable_income),
    'taxes': "{:,}".format(taxes),
    'alternative': "{:,}".format(alternative),
    'total_taxes': "{:,}".format(total_taxes),
    'effective_rate': effective_rate
  }
  return ret

if __name__ == "__main__":
  main()