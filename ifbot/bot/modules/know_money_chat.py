"""Basic personal-finance definitions plus a few small-talk courtesies.

Rule syntax: groups separated by '&'; each group lists alternatives separated by '|'.
A rule matches when EVERY group has at least one alternative present (after light
stemming). A group starting with '!' must have NO alternative present. More groups
means a more specific rule; the most specific match wins, ties go to the earlier rule.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Optional

from ..arbiter import Proposal

if TYPE_CHECKING:  # pragma: no cover
    from ..engine import Context


def _stem(w: str) -> str:
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 5 and w.endswith("ing"):
        return w[:-3]
    if len(w) > 4 and w.endswith("ed"):
        return w[:-2]
    if len(w) > 4 and w.endswith(("ses", "xes", "zes", "ches", "shes")):
        return w[:-2]
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w


MONEY = [
    # ---- budgeting ----
    ("budget & why|useful|important|benefit|point|need|good|help|worth",
     "A budget is useful because it shows where your money goes, so you can match spending to income and avoid running short before the next payday."),
    ("budget & make|create|start|build|set|write|plan|prepare|draw|how",
     "To make a budget, list the money you expect to receive, list your regular costs, and adjust spending so the costs do not exceed the income."),
    ("budget & stick|follow|keep|manage|track|review",
     "Keeping to a budget means tracking what you actually spend, comparing it with the plan, and adjusting the plan when your income or costs change."),
    ("budget|budgeting", "A budget is a plan that compares the money you expect to receive with the money you expect to spend."),
    ("need & want & difference|between|versus|vs|tell",
     "Needs are things you must have to live and work, such as food, housing and basic transport, while wants are things that are nice to have but you can do without."),
    ("frugal|frugality|thrifty|thrift", "Being frugal means spending carefully and avoiding waste, so your money lasts longer."),
    # ---- saving and investing ----
    ("saving|savings|save|saver & difference|versus|vs|between|compare|investing|investment|invest",
     "Saving keeps money safe and easy to reach, while investing puts money into assets that can rise or fall in value."),
    ("emergency & fund|savings|money|cash|account|reserve|why|useful",
     "An emergency fund is money set aside to cover unexpected costs, so you do not need to borrow when something goes wrong."),
    ("saving|savings|save|saver & why|important|useful|reason|point|benefit|good",
     "Saving is useful because money put aside can cover future needs and surprises without borrowing."),
    ("saving|savings|save|saver & account|bank",
     "A savings account is a bank account meant for keeping money you do not plan to spend soon, and the bank usually pays you some interest for leaving it there."),
    ("saving|savings|save|saver & goal|target|plan|habit|start|how|tip|ways",
     "A savings goal is a specific amount you want to set aside for a particular purpose, and putting a little aside regularly is a common way to reach it."),
    ("saving|savings & what|mean|define|definition",
     "Savings are the part of your income that you keep instead of spending."),
    ("investing|investment|invest & what|mean|define|definition|is",
     "Investing means putting money into things such as shares, bonds or property in the hope that they grow in value, which also carries the risk of losing some of it."),
    ("risk & invest|investing|investment|return|reward",
     "Investment risk is the chance that an investment loses value or earns less than expected, and in general higher possible returns come with higher risk."),
    ("stock|share|equity & market|company|what|mean|is|own|ownership",
     "A share, or stock, is a small piece of ownership in a company, and its price rises and falls with how the market values that company."),
    ("bond & government|company|what|mean|is|loan",
     "A bond is a loan you make to a government or company, which promises to pay you back later and usually pays interest in the meantime."),
    ("dividend", "A dividend is a share of a company's profit that it may pay out to the people who own its shares."),
    ("diversify|diversification|diversified|portfolio",
     "Diversification means spreading money across different kinds of assets, so a fall in one has less effect on the whole."),
    ("mutual|index & fund|etf", "A fund pools money from many people and invests it in a collection of assets, so each person owns a small slice of the whole collection."),
    ("pension|retirement & what|mean|is|why|save|fund|plan",
     "A pension or retirement plan is money set aside during working years so that you have an income when you stop working."),
    ("asset & what|mean|is|define|liability",
     "An asset is something you own that has value, such as cash, a home or shares, while a liability is something you owe."),
    ("net & worth", "Net worth is what you own minus what you owe."),
    ("liquid|liquidity", "Liquidity describes how quickly something can be turned into cash without losing much of its value."),
    ("compound & interest & growth|what|mean|is|saving|invest|how|work|define",
     "Compound interest is interest earned on both your original money and on the interest already added, so the amount grows faster over time."),
    ("simple & interest", "Simple interest is calculated only on the original amount, not on interest added earlier."),
    ("profit|revenue & what|mean|is|difference|business|company|between",
     "Revenue is the money a business takes in from sales, and profit is what is left after the costs are taken away."),
    # ---- interest, loans, debt ----
    ("interest & loan|borrow|mortgage|credit|debt|lender|pay|paying|charge|overdraft",
     "Interest is the extra amount you pay for borrowing money, usually shown as a percentage."),
    ("interest & rate|percentage|annual|apr|apy|what|mean|define|definition & !your|my|you|hobby|hobbies|favourite|favorite",
     "An interest rate is the cost of borrowing, or the reward for saving, shown as a percentage of the amount over a period of time."),
    ("interest & saving|savings|deposit|earn|account|bank",
     "Interest on savings is the money a bank pays you for keeping your money with it."),
    ("apr", "APR stands for annual percentage rate, which shows the yearly cost of a loan, including interest and some fees, as a percentage."),
    ("loan & what|mean|define|is|work|how|borrow",
     "A loan is money you borrow from a lender and agree to pay back over time, usually with interest."),
    ("loan & why|reason|take|need|people",
     "People take out loans to pay for something now that they cannot afford to pay for all at once, and then repay it over time."),
    ("loan & secured|unsecured|collateral",
     "A secured loan is backed by something valuable called collateral that the lender can claim if you do not repay, while an unsecured loan has no such backing."),
    ("collateral", "Collateral is something valuable that a borrower pledges to a lender, which the lender can keep if the loan is not repaid."),
    ("principal", "The principal is the original amount of money borrowed, not counting interest."),
    ("lender|borrower|creditor|debtor", "A lender is the person or organisation that provides money, and a borrower is the one who receives it and must pay it back."),
    ("mortgage", "A mortgage is a loan used to buy property, where the property itself is the security for the loan."),
    ("student & loan", "A student loan is money borrowed to pay for education that is paid back later, often after studies end."),
    ("repay|repayment|instalment|installment & loan|debt|what|mean|how|monthly|payment",
     "A repayment, or instalment, is one of the regular payments you make to pay back a loan over time."),
    ("minimum & payment", "A minimum payment is the smallest amount you must pay on a debt by its due date to avoid penalties."),
    ("late & fee|payment|penalty|bill|charge", "A late fee is an extra charge added when a payment is made after its due date."),
    ("debt & what|mean|define|is|owe",
     "Debt is money that you owe to someone else and must pay back."),
    ("debt & why|bad|danger|problem|trouble|careful|avoid|risk|cost",
     "Debt can become a problem because interest makes the amount owed grow, and repayments take a share of your future income."),
    ("debt & pay|clear|reduce|repay|off|manage|get|out",
     "Paying off debt means making payments that cover the interest and reduce the amount owed until nothing is left."),
    ("overdraft", "An overdraft lets you spend more than you have in your bank account, up to a limit, and the bank usually charges fees or interest on it."),
    ("bankrupt|bankruptcy", "Bankruptcy is a legal process for people or businesses who cannot repay their debts."),
    ("default & loan|debt|payment|credit", "To default on a loan means to fail to make the payments that were agreed."),
    # ---- credit ----
    ("credit & score|rating|report|show|mean|check",
     "A credit score gives lenders a rough idea of how reliably you have repaid money in the past."),
    ("credit & report", "A credit report is a record of your borrowing and repayment history that lenders can look at."),
    ("credit & card & what|mean|how|work|is|define",
     "A credit card lets you borrow money from the card company to pay for things, and you must pay it back, with interest if you do not clear the balance on time."),
    ("credit|debit & card & difference|versus|vs|between|compare",
     "A debit card takes money straight from your bank account, while a credit card spends money borrowed from the card company that you repay later."),
    ("debit & card", "A debit card is a bank card that pays for things using money that is already in your account."),
    ("credit & card & limit", "A credit limit is the most you are allowed to borrow on a credit card at one time."),
    ("credit & card & statement|bill|balance", "A credit card statement is a monthly summary of what you spent, what you owe and the payment due."),
    ("credit|build|improve|good|better|raise|history & how|score|history",
     "A credit history grows when you borrow and repay on time, and a record of late or missed payments can lower your score."),
    ("credit & what|mean|define", "Credit is an arrangement that lets you buy or borrow now and pay later."),
    ("contactless & card|pay|payment|what|mean", "Contactless payment lets you pay by tapping a card or phone on a reader instead of inserting the card or typing a code."),
    ("fraud|scam|fraudulent|skimming & card|bank|money|account|payment|identity",
     "Fraud is tricking someone to take their money or financial details, so keep your card details and codes private and check your statements for payments you do not recognise."),
    # ---- banking ----
    ("bank & account & what|mean|define|is|why|use|open|for",
     "A bank account is a service where a bank keeps your money safely, lets you pay and receive money, and records what comes in and out."),
    ("bank & what|mean|define|is|do|does|why|work|for",
     "A bank is a business that keeps your money safe, lends money to others and offers ways to pay and receive money."),
    ("checking|current & account", "A current or checking account is a bank account for everyday spending and receiving pay, where you can deposit and withdraw money easily."),
    ("deposit & what|mean|bank|make|account|is",
     "A deposit is money that you put into a bank account."),
    ("withdraw|withdrawal & what|mean|bank|account|cash|money|is",
     "A withdrawal is taking money out of your bank account, for example from a cash machine."),
    ("atm|cash-machine|cashpoint", "A cash machine, or ATM, lets you take out cash, check your balance and do other basic banking using your card and code."),
    ("pin & card|code|number|bank|what|atm|mean", "A PIN is a secret number that you enter to prove a card or account is yours, so never share it."),
    ("balance & account|bank|what|mean|check", "Your account balance is the amount of money in the account at a given moment."),
    ("bank & statement|statement", "A bank statement is a regular record listing the money going in and out of your account and your balance."),
    ("transfer & money|bank|account|what|mean|wire", "A bank transfer moves money from one account to another electronically."),
    ("direct & debit|standing & order",
     "A direct debit or standing order is an instruction that lets regular payments leave your account automatically."),
    ("online|mobile|internet & banking|bank", "Online or mobile banking lets you check your balance, pay bills and move money using a website or app instead of visiting a branch."),
    ("fee & bank|account|charge|monthly|atm|what|mean", "A bank fee is a charge a bank makes for a service, such as keeping an account or using a cash machine."),
    ("cheque|check & bank|pay|write|what|mean|paper", "A cheque is a written instruction telling your bank to pay a set amount to the person named on it."),
    ("joint & account", "A joint account is a bank account shared by two or more people who can all use the money in it."),
    ("interest & rate & bank|central", "A bank sets the interest it charges borrowers and pays savers, and these are affected by the wider economy."),
    # ---- cash and payments ----
    ("cash & card & difference|versus|vs|better|compare|between|or|why|use",
     "Cash is physical money you hand over directly, while a card pays electronically from your account or from credit, which leaves a record of the payment."),
    ("cash & what|mean|define|is", "Cash is physical money, such as notes and coins, that you can spend directly without needing an account."),
    ("currency & what|mean|define|is", "A currency is the money used in a particular country or region."),
    ("exchange & rate|currency|money|foreign", "An exchange rate tells you how much of one currency you get in return for another."),
    ("coin|note|banknote & what|money|made|cash", "Coins and banknotes are the physical forms of cash issued by a country."),
    ("payment & method|type|way|option|what", "Common ways to pay are cash, bank card, bank transfer and phone payment apps."),
    ("gift & card|voucher", "A gift card is a prepaid card or code with a set value that can be spent at a particular shop or group of shops."),
    ("prepaid|prepay & card|what|mean", "A prepaid card is a card you load with money in advance and can only spend up to what you loaded."),
    ("refund & what|mean|is|get|ask|return|receipt", "A refund is when a seller gives your money back after you return a product or cancel a service."),
    ("change & money|cash|coin|shop|give", "Change is the money handed back to you when you pay with more than the exact price."),
    # ---- income, expenses ----
    ("income & what|mean|define|is", "Income is the money you receive, for example from work, a business, benefits or investments."),
    ("expense|cost|spending & what|mean|define|is|type|kind",
     "An expense is money you spend, such as rent, food, transport and bills."),
    ("income & expense|expenses|spend|spending & difference|between|versus|vs|compare",
     "Income is the money coming in, and expenses are the money going out, so what is left is what you can save."),
    ("fixed & variable & expense|cost|spending|bill",
     "Fixed expenses stay the same each month, like rent, while variable expenses change, like groceries or fuel."),
    ("salary|wage|pay & what|mean|define|is|difference|between",
     "A salary is a fixed amount paid for a job regularly, while a wage is usually paid by the hour for the time worked."),
    ("gross|net|take-home|takehome & pay|income|salary|wage|difference|what|mean",
     "Gross pay is what you earn before deductions, while net or take-home pay is what you actually receive after tax and other deductions."),
    ("payslip|payroll|stub & what|mean|why|show|read|salary|wage",
     "A payslip is a record given with your pay that shows how much you earned and what was taken out, such as tax."),
    ("freelance|self-employed|selfemployed|contractor & income|pay|what|mean|work",
     "Being self-employed means you work for yourself and earn income from your own customers or clients instead of a regular salary."),
    ("profit & loss", "A business makes a profit when its income is more than its costs and a loss when its costs are more."),
    ("rent & what|mean|define|is|why|pay", "Rent is a regular payment you make to a landlord for the use of a home or other property."),
    ("tip|tipping|gratuity & restaurant|waiter|service|what|mean|why|bar|taxi",
     "A tip is a small extra amount of money given to someone who serves you, as thanks for good service."),
    ("subscription & what|mean|cancel|pay|charge|service|cost", "A subscription is a service you pay for regularly, such as monthly or yearly, until you cancel it."),
    ("allowance|pocket & money|child|kid", "Pocket money is a small regular amount given to a child to spend or save and learn about managing money."),
    # ---- prices, inflation ----
    ("inflation & what|mean|define|is",
     "Inflation is a general rise in prices over time, which means each unit of money buys a little less than before."),
    ("inflation & why|cause|happen|rise|go|affect|matter|important",
     "Inflation happens when prices across the economy keep rising, which can reduce what your money can buy."),
    ("deflation", "Deflation is a general fall in prices over time, the opposite of inflation."),
    ("cost & living & what|mean|is|define", "The cost of living is how much money you need to pay for basics like housing, food, transport and bills."),
    ("price & compare|comparison|shop|shopping|cheaper|cheapest|best|deal|find|check",
     "Comparing prices means checking what different sellers charge for the same thing, so you can see which gives better value for your money."),
    ("price & why|rise|change|vary|go|up|different|determine|set",
     "Prices change because of supply and demand, costs of making and delivering goods, and shop decisions, so the same item can cost different amounts at different times."),
    ("unit & price", "A unit price is the cost per single measure, such as per kilogram or per item, which lets you compare different pack sizes fairly."),
    ("price & what|mean|define|is", "A price is the amount of money a seller asks for a product or service."),
    ("discount|sale|coupon|voucher|offer & what|mean|is|work|how|why|real",
     "A discount is a reduction from the usual price, and it is worth checking the final amount you pay rather than just the size of the reduction."),
    ("value & money|worth|for", "Value for money means getting a good quality or benefit in return for what you pay."),
    ("supply & demand", "Supply is how much of something is available and demand is how much people want it, and together they influence its price."),
    ("economy|economic & what|mean|is|define", "The economy is the system of making, selling and buying goods and services in a country."),
    ("recession & what|mean|is|define", "A recession is a period when the economy shrinks, with less spending, fewer jobs and lower output."),
    ("gdp", "GDP, or gross domestic product, is the total value of goods and services produced in a country over a period of time."),
    # ---- tax ----
    ("tax|taxes|taxation & what|mean|define|is",
     "A tax is money that people and businesses must pay to the government, which uses it to fund public services."),
    ("tax|taxes|taxation & why|reason|pay|paying|purpose|use|for|need",
     "Taxes are paid so that the government can fund public services such as roads, schools, healthcare and security."),
    ("income & tax", "Income tax is a tax on the money you earn, usually taken from pay or paid after you report your income."),
    ("sales|vat|value-added|consumption|purchase & tax", "A sales tax, or VAT, is a tax added to the price of goods and services when you buy them."),
    ("property|council & tax", "A property tax is a tax paid by the owner of land or a building."),
    ("tax & return|filing|file|declaration|form", "A tax return is a form where you report your income to the tax authority and work out what tax is owed or refunded."),
    ("tax & deduction|deductible|allowance|credit|relief|exempt|exemption", "A tax deduction or allowance is an amount that lowers the income on which you pay tax."),
    ("tax & evasion|avoidance", "Tax evasion means illegally hiding income to pay less tax, while tax avoidance uses legal rules to reduce the tax owed."),
    ("tax & withhold|withholding|deduct|deducted|payslip|paycheck|paycheque", "Tax can be withheld, meaning your employer takes it from your pay and sends it to the tax authority for you."),
    ("tax & bracket|progressive|band", "Tax bands, or brackets, are ranges of income that are taxed at different rates."),
    ("customs|duty|import & tax|duties|what|mean", "A customs duty is a tax charged on goods brought into a country from abroad."),
    # ---- insurance ----
    ("insurance|insure|insured & what|mean|define|is|work|how",
     "Insurance is an agreement where you pay regular amounts to a company, and it covers certain losses or costs if something bad happens."),
    ("insurance|insure & why|need|reason|useful|important|point|worth|buy|get|have",
     "Insurance is useful because it protects you from a large unexpected cost by sharing the risk with many other people who pay in."),
    ("premium & insurance|what|mean|pay", "An insurance premium is the amount you pay regularly to keep your cover."),
    ("deductible|excess & insurance|claim|what|mean|pay", "A deductible, or excess, is the part of a claim that you pay yourself before the insurer pays the rest."),
    ("claim & insurance|insurer|policy|make|file|what|mean", "An insurance claim is a request to your insurer to pay for a loss that your policy covers."),
    ("policy & insurance|what|mean|insurer", "An insurance policy is the contract that states what is covered, for how long and at what cost."),
    ("health|medical & insurance|cover", "Health insurance helps pay for medical care, so a big treatment bill does not fall entirely on you."),
    ("car|vehicle|motor|auto & insurance", "Car insurance covers costs from accidents, damage or theft of a vehicle, and in many places it is required by law to have some cover."),
    ("home|house|contents|property & insurance", "Home insurance covers damage to a home or its contents from events such as fire, flooding or theft."),
    ("life & insurance", "Life insurance pays money to your family or chosen people if you die."),
    ("travel & insurance", "Travel insurance covers costs such as medical care, cancelled trips or lost luggage while you are away."),
    # ---- bills, receipts ----
    ("bill|bills & what|mean|define|is",
     "A bill is a request for payment for goods or services you have used, such as electricity, water or a phone."),
    ("bill|bills & pay|paying|due|when|late|miss|missed|how|on|time",
     "Bills should be paid by their due date, because late payments can bring extra charges and may affect your credit record."),
    ("bill|bills & why|reason|get|receive|monthly|regular|come",
     "Bills arrive regularly because services such as electricity, water and phones are used continuously and are charged for after use."),
    ("utility|utilities & bill|what|mean|is", "Utility bills are charges for basic services such as electricity, gas, water and internet."),
    ("invoice & what|mean|define|is|difference|bill|receipt", "An invoice is a document a seller sends to ask for payment, listing what was supplied and the amount due."),
    ("receipt & what|mean|define|is|show|contain",
     "A receipt is a record from a seller that proves you paid for something and shows what you bought, the amount and the date."),
    ("receipt & why|keep|save|need|important|useful|useful|reason|should|ask|get",
     "Receipts are worth keeping because they prove you paid, so you can return or exchange an item, claim a refund or check your spending later."),
    ("quote|estimate & what|mean|price|work|cost|difference", "A quote or estimate is a seller's statement of what a job or product will cost before you agree to buy."),
    ("deposit & shop|booking|reservation|hold|refundable|rent",
     "A deposit in a purchase or booking is an amount paid up front to reserve something, which counts toward the total or is returned depending on the terms."),
    ("warranty|guarantee & money|refund|purchase|buy", "A guarantee is a promise from a seller to repair, replace or refund a product that fails within a set period."),
    ("record|track|tracking & spending|expense|money|finance|finances", "Tracking spending means writing down or reviewing what you pay for, using receipts, a notebook, a spreadsheet or an app, so you know where your money goes."),
    ("financial|finance|money & literacy|education|what|mean", "Financial literacy is knowing enough about money, such as budgeting, saving, borrowing and interest, to make informed decisions."),
    ("money & what|mean|define|is|why|use|for|exist", "Money is something people accept in exchange for goods and services, which makes buying, selling and saving easier than trading goods directly."),
    ("barter|swap & trade|goods|money", "Bartering means trading goods or services directly for other goods or services without using money."),
    ("wealth|rich & what|mean|define|is|difference|income", "Wealth is the total value of what a person owns minus what they owe, while income is the money received over a period."),
    ("afford|affordable|affordability & what|mean|define|is", "If something is affordable, you can pay for it from your income without being unable to cover your other needs."),
    ("overspend|overspending & why|what|mean|happen|avoid|stop", "Overspending means spending more than you planned or earn, and a budget helps you notice it early."),
    ("impulse & buy|buying|purchase|spend|spending|shopping", "An impulse purchase is something you buy on a sudden urge without planning it."),
    ("charity|donation|donate & what|mean|money|tax", "A donation is money or goods given to a person or cause without expecting anything in return."),
    ("estate|inheritance|will & money|property|what|mean|inherit", "An inheritance is money or property passed on to someone after a person dies."),
]

SMALL = [
    # ---- asking for help ----
    ("help & can|could|will|would|need|please|me|want|i & !what|how|why|when|which|where|who|thank|thanks|budget|loan|tax|bank|money|price|interest|credit",
     "Happy to lend a hand. Tell me what you are stuck on and I will try my best."),
    ("help|assist & !what|how|why|when|which|where|who|thank|thanks|can|could|will|would|need|please|me|want|i|you",
     "I am right here. Say what you need and I will see what I can do."),
    ("question & have|got|ask|can|may|could|i & !what|how|why|when|which|where|who",
     "Go right ahead and ask it. I will give it my best shot."),
    ("something & ask|tell|say|show & can|may|could|i|let|want|need",
     "Sure thing, go ahead whenever you are ready and I will listen."),
    # ---- meeting and feelings ----
    ("nice|pleased|glad|good|great|lovely|happy|pleasure & meet|meeting|know & you",
     "The pleasure is mine. I am glad we got talking, so what would you like to chat about?"),
    ("nice|good|great|lovely & see & you", "Lovely to see you too. What can I do for you today?"),
    ("welcome & back", "Thanks, it is good to have you back. What shall we pick up?"),
    ("long & time & no|since & see|talk|speak|hear", "It has been a while indeed. Glad you dropped in, so how can I help?"),
    ("how & your & day|morning|evening|afternoon|week|weekend|night & !my",
     "My day is going smoothly, thanks for asking. How is yours, and can I help with anything?"),
    ("how & go|going & it|things|everything|life & !my",
     "Things are ticking along nicely on my side. How are things with you, and what can I do for you?"),
    ("what & up & !with|about|for|in|on|you|is", "Not much is new at my end. What is on your mind?"),
    ("what & new & with & you|your", "Nothing big is new here, but I am ready to chat. What about you?"),
    ("how & do & you & do", "I do just fine, thank you. How can I be of use?"),
    ("what & you & doing|up|busy & !to", "I was waiting for a message like yours. What would you like to talk about?"),
    ("you & there|awake|listening|ready|busy|free|around & are|re", "Yes, I am here and listening. Go on whenever you like."),
    ("can & you & hear|see & me", "I read what you type, so I am following along. Go on."),
    ("i|me|am|feel|feeling & happy|excited|glad|great|wonderful|fantastic|awesome|good|fine|well|alright|okay|ok|pleased & !not",
     "That is good to hear. Is there something I can do to make your day a bit better still?"),
    ("i|me|am|feel|feeling & sad|down|unhappy|lonely|blue|upset|stressed|worried|anxious",
     "I am sorry you feel that way. I am happy to keep you company, so tell me what is going on if you want to."),
    ("i|me|am|feel|feeling & tired|sleepy|exhausted|bored|busy",
     "That sounds like a long stretch. Take it easy, and tell me if there is anything I can do for you."),
    ("i & love|like & you", "That is very sweet of you to say. I am glad you enjoy chatting, so what next?"),
    ("alone|lonely|company|bored & keep|me|feel|am|i", "I am happy to sit with you for a bit. What would you like to talk about?"),
    ("let|can|want|wanna|shall & chat|talk|speak|converse & us|we|you|with|to",
     "I would enjoy that. Pick a topic and we will take it from there."),
    ("talk|chat|speak & to|with & me", "Of course, I am all ears. What is on your mind?"),
    # ---- sorry, praise ----
    ("sorry|apologize|apologise|apologies|oops|pardon|forgive & !what|how|why|when|where|which|who",
     "No harm done at all. Let us carry on, and tell me what I can do for you."),
    ("my & bad|fault|mistake|mistake", "Nothing to worry about, these things happen. How can I help from here?"),
    ("excuse & me", "Yes, I am listening. What did you want to say?"),
    ("you & are|re|were & great|awesome|amazing|smart|clever|helpful|nice|kind|cool|brilliant|funny|wonderful|fantastic|best|sweet|good|lovely|right|useful & !not|never",
     "That is generous of you. I am pleased to be useful, so is there anything else I can look at?"),
    ("good|great|nice|excellent|fine|well|amazing & job|work|answer|bot|one|response",
     "Thank you, that makes my day. Let me know what else I can help you with."),
    ("well & done", "Much appreciated. Shout if you need anything else from me."),
    ("good & point|idea|call|thinking", "Glad that landed well. Shall we go on, or is there something else to look at?"),
    ("appreciate|appreciated|cheers|grateful|thankful & you|it|that|help|your|this|so|much|really",
     "It was my pleasure. Come back anytime you need a hand."),
    ("wrong|incorrect|mistaken|useless|bad & you|are|that|answer|is|was|not",
     "Sorry about the mix-up. Try asking it in different words and I will give it another go."),
    ("not & what & i & asked|meant|wanted|said", "Sorry I missed it. Could you put it another way so I can try again?"),
    # ---- agreement, short replies ----
    ("yes|yeah|yep|yup|sure|ok|okay|alright|agreed|exactly|indeed|absolutely|definitely|true|correct|right|fine|certainly|agree & !not|no|what|how|why|when|where|which|who|thank|thanks|hello|hi|hey|bye|goodbye",
     "Great, we are on the same page. What would you like to do next?"),
    ("no|nope|nah|not & thanks|now|really|today", "That is fine. I am here if you change your mind about anything."),
    ("i & agree|understand|see|get & !not|do", "Good, glad that makes sense. Ask away if anything else comes up."),
    ("got|understood|noted & it|that", "Perfect. Tell me if anything else comes up."),
    ("makes & sense", "Glad it is clear. Ask me more if you wish."),
    ("fair & enough|point", "Thanks for being understanding. Anything else I can help with?"),
    ("maybe|perhaps|guess|suppose|possibly & i|so|not|think|sure|know", "No rush at all. Take your time, and ask me when you are ready."),
    ("cool|nice|awesome|great|excellent|perfect|wonderful|lovely|brilliant|fantastic|neat|sweet|super & !not|no|what|how|why|when|where|which|who",
     "Glad that works for you. Is there anything else I can help with?"),
    ("haha|hahaha|lol|lmao|funny|hehe & !not", "Glad that brought a smile. Anything else I can help you with?"),
    ("wait|hold & on|up|a|one|just|please", "Of course, take all the time you need. I will be right here."),
    ("one|a|few|second|moment|minute & give|just|moment|hold|wait", "No problem, take your moment. I am not going anywhere."),
    ("repeat|again & say|can|could|please|that|it", "Sure. Please ask me once more, perhaps in different words, and I will try again."),
    ("what & you & say|said|mean|meant & did|do", "Sorry if I was unclear. Ask again in your own words and I will try a fresh answer."),
    ("not|do|did & understand|get & you|it|that|what & i|do|did", "Apologies for the confusion. Tell me which part was unclear and I will try again."),
    ("come & again", "Sure, ask me once more in other words and I will have another go."),
    # ---- identity small questions ----
    ("are & you & robot|human|real|person|bot|machine|ai|program|alive|computer",
     "I am a small computer program, not a person, but I do enjoy a good chat."),
    ("where & you & from|live|come|located", "I live inside a computer program, so I do not really have a hometown."),
    ("how & old & you", "I have no birthday to speak of, since I am just a small program."),
    ("do & you & speak|understand|know & language|english|arabic|french|spanish", "I chat in English, and I do my best to follow what you write."),
    ("are & you & happy|ok|okay|fine|well|alright", "I am in good spirits, thank you for asking. How about you?"),
    ("do & you & feel|have & feelings|emotions", "I do not have feelings the way people do, but I like being useful to you."),
    # ---- partings, occasions ----
    ("take|have & care|nice|good|great|lovely & day|evening|weekend|one|night|week|trip",
     "Same to you, and come back anytime you want to chat."),
    ("i & must|have|got|need|should & go|leave|run|leaving|off", "Alright then, off you go. Drop in again whenever you like."),
    ("see & you & soon|tomorrow|next|then|around|again", "See you then, and have a smooth rest of your day."),
    ("talk|catch|speak & later|soon|tomorrow|you", "Talk to you then. Come back whenever you feel like it."),
    ("bye & for|now|bye", "Bye for now, and thanks for stopping by."),
    ("happy|merry|blessed & birthday|christmas|year|holidays|holiday|easter|friday|monday|eid|ramadan|diwali|hanukkah",
     "Thank you, and the same wishes to you. Is there anything I can help with today?"),
    ("eid|ramadan & mubarak|kareem", "Mubarak to you as well. May the days ahead be gentle. Anything I can help with?"),
    ("congratulations|congrats|cheers & to|on|you", "Thank you kindly. Let me know if I can help with anything."),
    ("good & luck", "Thank you, and good luck to you too. Tell me if you need anything."),
    ("wish & luck|me", "Wishing you the very best of luck. I will be here if you need anything."),
    ("have & fun|enjoy|good|great & time|meal|trip|evening", "You too, enjoy yourself. I am here if you need anything."),
    ("no & problem|worries|prob|trouble|bother|worry", "Glad that is fine. Ask me whenever something else comes up."),
    ("never|nevermind|forget & mind|it|about", "Alright, no problem. Ask me anything else whenever you like."),
    ("welcome & you|are|re|my", "Glad you feel that way. Is there anything else I can help you with?"),
    ("pleasure & my|it|was|mine", "Kind of you to say. Ask me anything else anytime."),
    ("say|tell & something|anything & me|to|say|tell", "Here is a small thing: I enjoy being asked questions, so ask me one. What are you curious about?"),
    ("entertain|surprise|amuse & me", "I will do my best with a chat. Ask me a question and we will see where it goes."),
    ("nothing|nothing & say|much|to|happen", "That is fine, silence is allowed here. Ask me whenever something comes up."),
]


def _compile(rules):
    out = []
    for spec, answer in rules:
        pos, neg = [], []
        for g in spec.split("&"):
            g = g.strip().lower()
            if not g:
                continue
            is_neg = g.startswith("!")
            if is_neg:
                g = g[1:]
            alts = {_stem(a.strip()) for a in g.split("|") if a.strip()}
            if alts:
                (neg if is_neg else pos).append(alts)
        out.append((pos, neg, answer))
    return out


_MONEY = _compile(MONEY)
_SMALL = _compile(SMALL)
_WORD = re.compile(r"[a-z0-9-]+")
_SMALL_MAX_TOKENS = 10


def _best(compiled, toks):
    best, best_key = None, None
    for idx, (pos, neg, answer) in enumerate(compiled):
        if not pos or not all(g & toks for g in pos):
            continue
        if any(g & toks for g in neg):
            continue
        key = (len(pos), -idx)
        if best_key is None or key > best_key:
            best_key, best = key, answer
    return best, best_key


def propose(ctx: "Context") -> Optional[Proposal]:
    toks = set()
    for t in ctx.tokens:
        toks.add(_stem(t))
    for t in _WORD.findall(ctx.text):
        toks.add(_stem(t))
    if not toks:
        return None
    answer, key = _best(_MONEY, toks)
    if answer is not None:
        return Proposal(answer, min(0.72 + 0.03 * (key[0] - 1), 0.8))
    if len(ctx.tokens) <= _SMALL_MAX_TOKENS:
        answer, key = _best(_SMALL, toks)
        if answer is not None:
            return Proposal(answer, min(0.6 + 0.04 * (key[0] - 1), 0.72))
    return None
