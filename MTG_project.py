# %% [markdown]
# <!-- ---
# title: "Do winning decks in MTG World Championships have a particular card balance?"
# author: "Paolo Saracco"
# date: "2024-05-14"
# output:
#         bookdown::html_document2:
#                 fig_caption: true
#                 toc: true
#                 toc_depth: 2
#                 toc_float: 
#                         collapsed: true
#                 number_sections: false
#                 keep_md: true
# --- -->
# # Do winning decks in MTG World Championships have a particular card balance?
# 
# author: Paolo Saracco
# 
# date: 2024-05-14
# 
# ## Executive summary
# 
# *Magic: The Gathering* (aka MTG) is a well-known collectible card game created by Richard Garfield. The MTG World Championships (Worlds) is among the most important tournament in the game, offering cash prizes of up to $100,000 to the winners. We wonder whether winning decks in the standard format have a particular combination of different card types. To answer the question in the negative, we compare the number of Land, Creature, Instant and Sorcery, and Other card types in the top 4 decks of each World Championship from 1994 until 2022.
# 
# ## Libraries

# %%
import requests
import re
from bs4 import BeautifulSoup
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import seaborn as sns
from statistics import mean
import scipy.stats as ss
import os

# %% [markdown]
# ## Data set
# 
# To collect the data we need, we scrape the webpage [www.mtgtop8.com](https://www.mtgtop8.com/) and we save the outcome in a csv file called `raw_magic.csv`.

# %%
folder = os.getcwd()
data_dir = Path(folder, "data")
Path(data_dir).mkdir(parents=True, exist_ok=True)
data_file = Path(data_dir, "raw_magic.csv")

if not data_file.exists() :
    print(f"{data_file} does not exists. Creating it...")

    players = pd.DataFrame(columns = ["Deck", "Player", "Format", "Event", "Level", "Rank", "Date"])
    decks = pd.DataFrame()

    for year in range(1994,2023,1) :
        # we skip year 2023 because there are decks with empty name field and
        # the command < data = row.text.strip().split("\n\t\t  ") >
        # produces a list which is shorter than the others,
        # running into the error
        # < ValueError: cannot set a row with mismatched columns >
        print(f"I am scraping year {year}")

        my_status = 200
        deck_rows = ["some rows..."]
        page = 1

        while my_status == 200 and deck_rows != [] :
            # gets the content of the page corresponding to
            # searching with the parameters given below
            url = "https://www.mtgtop8.com/"
            parameters = {"current_page" : f"{page}", 
                        "event_titre" : "world",
                        "format" : "ST",
                        "compet_check[P]" : "1",
                        "date_start" : f"01/01/{year}",
                        "date_end" : f"31/12/{year}"}
            response = requests.get(url + "search", params = parameters)
            my_status = response.status_code

            if my_status == 200 :

                soup = BeautifulSoup(response.text, "html5lib")

                deck_rows = soup.find_all("tr", class_ = "hover_tr")

                if deck_rows == [] :
                    print(f"Finished with year {year}. Moving to the next...")

                else :
                    # extract the table on the given page
                    # and concatenates it to the "players"
                    for row in deck_rows :
                        data = row.text.strip().split("\n\t\t  ")
                        players.loc[len(players)] = data

                    # extracts the links to the decks on the given page
                    deck_links = soup.find_all("a", href = re.compile(".*&d=.*"))

                    # for each link, it scrapes the info about the deck
                    # and concatenats it to the "decks"
                    deck_cards = []

                    for link in deck_links :
                        print(f"I am scraping year {year}, deck : {link.text}")
                        new_deck_url = url + link["href"]
                        response_new_deck = requests.get(new_deck_url)
                        soup_new_deck = BeautifulSoup(response_new_deck.text, "html5lib")
                        details_new_deck = soup_new_deck.find_all("div", class_ = "O14")
                        new_deck = {}
                        for elem in details_new_deck :
                            text_string = elem.text
                            text_string_list = text_string.split()
                            name = ""
                            value = 0
                            for text in text_string_list :
                                if text.isdigit() :
                                    value = int(text)
                                else :
                                    name = name + text + "_"
                            new_deck[f"{name.strip("_")}"] = value

                        deck_cards.append(pd.DataFrame(new_deck, index = [0]))
                
                    deck_cards = pd.concat(deck_cards, ignore_index=True)
                    decks = pd.concat([decks, deck_cards], ignore_index=True)

                    page += 1

            else :
                print(f"Status code page {page} or year {year} : {my_status}.")

    df = pd.concat([players,decks], axis=1)
    df.to_csv("data/raw_magic.csv", index=False)
    print("File created.")

else :
    print("File already existing. Scraping skipped.")

df = pd.read_csv(data_file)

# %% [markdown]
# ## Data cleaning

# %%
df.head()

# %%
data = df.copy()
data = data.drop(labels = ["Level","SIDEBOARD",'Format'], axis = 1)
data["Date"] = data["Date"].apply(lambda date : datetime.datetime.strptime(date, "%d/%m/%y"))
print("\n".join(data.Event.unique()))

# %% [markdown]
# First of all, we are only interested in the individual World Championship rankings. 
# 
# From [Wikipedia](https://en.wikipedia.org/w/index.php?title=Magic:_The_Gathering_World_Championship&oldid=1214619541):
# 
# *In 2012, the Magic World Championship structure was drastically altered alongside changes to the ranking system used in Magic: The Gathering. The individual World Championship was changed from a Pro Tour-sized event to a sixteen-player event, which was called the Magic Players Championship (though the tournament reverted to being called the World Championship for 2013). The team event, formerly held alongside the individual event, took place before the individual tournament and was contested by four-player teams instead of the previous three-player teams.*
# 
# *Team World Championship*
# *The Team World Championship consists of three-player teams, with each team representing one country. Players that are eligible to play in the Team World Championship are the first, second and third place players at a country's National Championship.*
# 
# *World Magic Cup*
# *In 2012, the Team World Championship became a single separate event called the 'World Magic Cup'. This national team event consists of four-player teams representing selected countries. The four players eligible to play in each national team will be the three winners of World Magic Cup qualifiers and the National Champion (the player finished with most Pro Points in previous season) of the country. The National Champion is the highest ranked player from that country in that year's rankings.* 
# 
# This means we do not consider the Pro Tours, including the 2012 Pro Tour that replaced the World Championship, and we drop the lines corresponding to the World Cups. 
# 
# Moreover, in 2011: *The eighteenth Magic World Championship was held from 17 to 20 November in the Fort Mason Center in San Francisco, the same site that already hosted the 2004 World Championship. The tournament consisted of six rounds of Standard on Thursday, two Innistrad Booster Drafts of three rounds each on Friday, and six rounds of Modern on Saturday. This would be the first World Championship to feature the new Modern format. On Sunday, the Top 8 players played against each other in elimination rounds, using the Standard decks they played on Thursday.*
# 
# We are only interested in the Top 8.

# %%
data = data[~data['Event'].str.contains('Cup')]
data = data[~data['Event'].str.contains('Undefeated')]
data = data[~data['Event'].str.contains('15 points')]
print("\n".join(data.Event.unique()))

# %% [markdown]
# Then we check how the rankings appear in the data.

# %%
print(data.Rank.unique())

# %% [markdown]
# By inspecting the Wikipedia page, we realise that in modern days it happens that the standard format is used only for the Top 4 on the last day:
# 
# *The 2016 World Championship was held from 1–4 September in Seattle. The formats used in the competition were Eldritch Moon-Shadows over Innistrad Booster Draft for rounds 1–3, Standard for rounds 4–7, Eldritch Moon-Shadows over Innistrad Booster Draft for rounds 8–10, Modern for rounds 11–14, and Standard for the Top 4.*
# 
# *The 2017 World Championship was held from 6–8 October in Boston. For the 2017 World Championship Wizards of the Coast decided to simplify the invitation criteria, awarding a large portion of invites to the players with the most Pro Points in the 2016–17 Pro Tour season. The formats used in the competition were Ixalan Booster Draft for rounds 1–3, Standard for rounds 4–7, Ixalan Booster Draft for rounds 8–10, Standard for rounds 11–14, and Standard for the Top 4.*
# 
# By Virtue of this observation, we select only the decks which are among the top 4 in every year, dropping everything else.
# 
# All the `Day 1 undefeated` ranked 9th or above:

# %%
print('Dates in which we have Day 1 undefeated rankings :')
for date in data[data['Rank'] == 'Day 1 undefeated'].Date.unique() :
    print(date.date())
    print('rankings : ' + str(data[data['Date'].dt.year == date.year].Rank.unique()))

# %% [markdown]
# Since we are interested only in the top 4 ranked decks, we will drop these harmlessly. Concerning the `NaN`'s, instead:

# %%
print('Dates in which we have NaN rankings :')
for date in data[pd.isna(data['Rank'])].Date.unique() :
    print(date.date())
    print('rankings : ' + str(data[data['Date'].dt.year == date.year].Rank.unique()))

# %% [markdown]
# All the NaN's ranked 5th or above, so we will drop them harmlessly. Concerning the `Other` rankings:

# %%
print('Dates in which we have Other rankings :')
for date in data[data['Rank'] == 'Other'].Date.unique() :
    print(date.date())
    print('rankings : ' + str(data[data['Date'].dt.year == date.year].Rank.unique()))

# %% [markdown]
# Again, all of them ranked 5th or above, so we will drop them harmlessly. 
# 
# Finally, the year 2014 has some issues: we correct it by checking the Wikipedia page by hands.
# 
# *The final standings were as follows:*
# - *Israel Shahar Shenhar (2013 World Champion) - Decklist*
# - *United States Patrick Chapin (Pro Tour Journey into Nyx winner)*
# - *Japan Yuuya Watanabe (Pro Point leader Japan)*
# - *Japan Kentaro Yamamoto (8th most Pro Points of otherwise unqualified)*

# %%
data.loc[data['Date'].dt.year == 2014,'Rank'] = np.NaN
data.loc[(data['Date'].dt.year == 2014) & (data['Player'] == 'Shahar Shenhar'),'Rank'] = '1'
data.loc[(data['Date'].dt.year == 2014) & (data['Player'] == 'Patrick Chapin'),'Rank'] = '2'
data.loc[(data['Date'].dt.year == 2014) & (data['Player'] == 'Yuuya Watanabe'),'Rank'] = '3'
data.loc[(data['Date'].dt.year == 2014) & (data['Player'] == 'Kentaro Yamamoto'),'Rank'] = '4'

# %% [markdown]
# We can now proceed to select only the observations of interest:

# %%
data = data[data['Rank'].isin(['1', '2', '3', '4', '3-4'])]

# %% [markdown]
# One final issue comes from the fact that there are decks, from a certain moment on, in which there are cards with two faces, and one face is a land. Hence the scraped data contain in parenthesis the max number of lands the deck can count on, generating new columns. 

# %%
print(", ".join(data.columns))

# %% [markdown]
# To begin with, I will try to consider them as non-lands.
# 

# %%
lands_columns = [col for col in data.columns if "LANDS" in col]

for i in data.index :
    for col in lands_columns :
        if not pd.isna(data.loc[i,col]) : 
            data.loc[i,"Lands"] = data.loc[i,col]

data = data.drop(labels = lands_columns, axis = 1)
data = data.rename(columns = {"CREATURES" : "Creatures",
                          "INSTANTS_and_SORC." : "Instants_Sorceries", 
                          "OTHER_SPELLS" : "Other_spells"})

# %% [markdown]
# Commenting the previous Python script and uncommenting the underlying Python script will consider them as lands.

# %%
# for i in data.index :
#     if not pd.isna(data.loc[i,'LANDS_(26)']) :
#         data.loc[i,"Lands"] = 26
#     elif not pd.isna(data.loc[i,'LANDS_(27)']) :
#         data.loc[i,"Lands"] = 27
#     elif not pd.isna(data.loc[i,'LANDS_(28)']) :
#         data.loc[i,"Lands"] = 28
#     elif not pd.isna(data.loc[i,'LANDS_(29)']) :
#         data.loc[i,"Lands"] = 29
#     else :
#         data.loc[i,"Lands"] = data.loc[i,"LANDS"]

# lands_columns = [col for col in data.columns if "LANDS" in col]

# data = data.drop(labels = lands_columns, axis = 1)
# data = data.rename(columns = {"CREATURES" : "Creatures",
#                           "INSTANTS_and_SORC." : "Instants_Sorceries", 
#                           "OTHER_SPELLS" : "Other_spells"})

# %% [markdown]
# To proceed with the data cleaning phase, let us seek additional `NaN`'s.

# %%
pd.isna(data).sum(axis=0)

# %% [markdown]
# Creatures, Lands and Other spells might not be an issue (see later), but Lands are:

# %%
data[np.isnan(data['Lands'])]

# %% [markdown]
# Inspecting mtgtop8 reveals that the composition of this deck is unknown. We are forced to drop it.

# %%
data = data[~np.isnan(data['Lands'])]
pd.isna(data).sum(axis=0)

# %% [markdown]
# In all the other cases, the NaN value shall be a 0:

# %%
data[pd.isna(data['Creatures'])]

# %%
data[pd.isna(data['Other_spells'])]

# %%
data = data.fillna(0)

# %% [markdown]
# To conclude, we need to adjust the rankings:

# %%
data.value_counts(subset = ["Rank"])

# %% [markdown]
# We have 43 `3-4` rankings. we add them by hands checking on [Wikipedia 13/05/2024](https://en.wikipedia.org/w/index.php?title=Magic:_The_Gathering_World_Championship&oldid=1214619541) (and we also correct two typos in the player names).

# %%
data.loc[(data['Date'].dt.year == 1994) & (data['Player'] == 'Dominic Symens'),'Rank'] = '3'
data.loc[(data['Date'].dt.year == 1994) & (data['Player'] == 'Cyrille de Foucaud'),'Rank'] = '4'
data.loc[(data['Date'].dt.year == 1995) & (data['Player'] == 'Henry Stern'),'Rank'] = '3'
data.loc[(data['Date'].dt.year == 1996) & (data['Player'] == 'Henry Stern'),'Rank'] = '3'
data.loc[(data['Date'].dt.year == 1996) & (data['Player'] == 'Olle Råde'),'Rank'] = '4'
data.loc[(data['Date'].dt.year == 1997) & (data['Player'] == 'Paul McCabe'),'Rank'] = '3'
data.loc[(data['Date'].dt.year == 1997) & (data['Player'] == 'Svend Sparre Geertsen'),'Rank'] = '4'
data.loc[(data['Date'].dt.year == 1998) & (data['Player'] == 'Jon Finkel'),'Rank'] = '3'
data.loc[(data['Date'].dt.year == 1998) & (data['Player'] == 'Raphael Levy'),'Rank'] = '4'
data.loc[(data['Date'].dt.year == 1999) & (data['Player'] == 'Raffaele Lo Moro'),'Rank'] = '3'
data.loc[(data['Date'].dt.year == 1999) & (data['Player'] == 'Matt Linde'),'Rank'] = '4'

data.loc[(data['Date'].dt.year == 2000) & (data['Player'] == 'Dominik Hothow'),'Rank'] = '3'
data.loc[(data['Date'].dt.year == 2000) & (data['Player'] == 'Benedikt Klauser'),'Rank'] = '4'
data.loc[(data['Date'].dt.year == 2001) & (data['Player'] == 'Antoine Ruel'),'Rank'] = '3'
data.loc[(data['Date'].dt.year == 2001) & (data['Player'] == 'Andrea Santin'),'Rank'] = '4'
data.loc[(data['Date'].dt.year == 2002) & (data['Player'] == 'Diego Ostrovich'),'Rank'] = '3'
data.loc[(data['Date'].dt.year == 2002) & (data['Player'] == 'Dave Humpherys'),'Rank'] = '4'
data.loc[(data['Date'].dt.year == 2003) & (data['Player'] == 'Tuomo Nieminen'),'Rank'] = '3'
data.loc[(data['Date'].dt.year == 2003) & (data['Player'] == 'David Humpherys'),'Rank'] = '4'
data.loc[(data['Date'].dt.year == 2004) & (data['Player'] == 'Ryou Ogura'),'Rank'] = '3'
data.loc[(data['Date'].dt.year == 2004) & (data['Player'] == 'Manuel Bevand'),'Rank'] = '4'
data.loc[(data['Date'].dt.year == 2005) & (data['Player'] == 'Tomohiro Kaji'),'Rank'] = '3'
data.loc[(data['Date'].dt.year == 2005) & (data['Player'] == 'Akira Asahara'),'Rank'] = '4'

data.loc[(data['Date'].dt.year == 2006) & (data['Player'] == 'Nicholas Lovett'),'Rank'] = '3'
data.loc[(data['Date'].dt.year == 2006) & (data['Player'] == 'Gabriel Nassif'),'Rank'] = '4'
data.loc[(data['Date'].dt.year == 2007) & (data['Player'] == 'Gabriel Nassif'),'Rank'] = '3'
data.loc[(data['Date'].dt.year == 2007) & (data['Player'] == 'Kotaro Otsuka'),'Rank'] = '4'
data.loc[(data['Date'].dt.year == 2008) & (data['Player'] == 'Tsuyoshi Ikeda'),'Rank'] = '3'
data.loc[(data['Date'].dt.year == 2008) & (data['Player'] == 'Hannes Kerem'),'Rank'] = '4'
data.loc[(data['Date'].dt.year == 2009) & (data['Player'] == 'Terry Soh'),'Rank'] = '3'
data.loc[(data['Date'].dt.year == 2009) & (data['Player'] == 'Bram Snepvangers'),'Rank'] = '4'
data.loc[(data['Date'].dt.year == 2010) & (data['Player'] == 'Paulo Vitor Damo da Rosa'),'Rank'] = '3'
data.loc[(data['Date'].dt.year == 2010) & (data['Player'] == 'Love Janse'),'Rank'] = '4'

data.loc[(data['Date'].dt.year == 2011) & (data['Player'] == 'Conley Woods'),'Rank'] = '3'
data.loc[(data['Date'].dt.year == 2011) & (data['Player'] == 'David Caplan'),'Rank'] = '4'
data.loc[(data['Date'].dt.year == 2013) & (data['Player'] == 'Ben Stark'),'Rank'] = '3'
data.loc[(data['Date'].dt.year == 2013) & (data['Player'] == 'Josh Utter-Leyton'),'Rank'] = '4'
data.loc[(data['Date'].dt.year == 2016) & (data['Player'] == 'Oliver Tiu'),'Rank'] = '3'
data.loc[(data['Date'].dt.year == 2016) & (data['Player'] == 'Shota Yasooka'),'Rank'] = '4'
data.loc[(data['Date'].dt.year == 2017) & (data['Player'] == 'Josh Utter-leyton'),'Rank'] = '3'
data.loc[(data['Date'].dt.year == 2017) & (data['Player'] == 'Kelvin Chew'),'Rank'] = '4'
data.loc[(data['Date'].dt.year == 2018) & (data['Player'] == 'Benjamin Stark'),'Rank'] = '3'
data.loc[(data['Date'].dt.year == 2018) & (data['Player'] == 'Shahar Shenhar'),'Rank'] = '4'

data.loc[(data['Date'].dt.year == 2013) & (data['Player'] == 'Ben Stark'),'Player'] = 'Benjamin Stark'
data.loc[(data['Date'].dt.year == 2017) & (data['Player'] == 'Josh Utter-leyton'),'Player'] = 'Josh Utter-Leyton'

data['Rank'] = data['Rank'].astype('category')
data.value_counts(subset = ["Rank"])

# %% [markdown]
# We can now work with our cleaned data set:

# %%
data.to_csv("data/magic.csv", index=False)

folder = os.getcwd()
cleaned_data = Path(folder, "data", "magic.csv")
data = pd.read_csv(cleaned_data)

data["Date"] = data["Date"].apply(lambda date : datetime.datetime.strptime(date, "%Y-%m-%d"))
data['Rank'] = data['Rank'].astype('category')

# %% [markdown]
# ## Exploratory data analysis

# %%
data.head()

# %%
data.describe()

# %% [markdown]
# A first interesting question is to see the evolution of the composition of decks along time.

# %%
data_mean_byYear = data[['Date','Creatures','Instants_Sorceries','Other_spells','Lands']].groupby('Date', observed=False).mean()
figure, axis = plt.subplots(2, 2, figsize=(12,8)) 

axis[0,0].plot(data_mean_byYear["Lands"], 'r.-', label='Lands')
axis[0,0].set(xlabel='Lands',ylabel='Count')
axis[0,1].plot(data_mean_byYear["Creatures"], 'b.-', label='Creatures')
axis[0,1].set(xlabel='Creatures',ylabel='Count')
axis[1,0].plot(data_mean_byYear["Instants_Sorceries"], 'g.-', label='Instants & Sorceries')
axis[1,0].set(xlabel='Instants & Sorceries',ylabel='Count')
axis[1,1].plot(data_mean_byYear["Other_spells"], 'y.-', label='Other spells')
axis[1,1].set(xlabel='Other spells',ylabel='Count')

plt.show()

# %% [markdown]
# Another interesting question is to see the evolution of the composition of the top ranked decks over time.

# %%
Champs = data[data["Rank"] == 1]
Champs = Champs.reset_index().drop(['index','Rank'], axis=1)

figure, axis = plt.subplots(2, 2, figsize=(12,8)) 

axis[0,0].plot(Champs["Date"], Champs["Lands"], 'r.-', label='Lands')
axis[0,0].set(xlabel='Lands',ylabel='Count')
axis[0,1].plot(Champs["Date"], Champs["Creatures"], 'b.-', label='Creatures')
axis[0,1].set(xlabel='Creatures',ylabel='Count')
axis[1,0].plot(Champs["Date"], Champs["Instants_Sorceries"], 'g.-', label='Instants & Sorceries')
axis[1,0].set(xlabel='Instants & Sorceries',ylabel='Count')
axis[1,1].plot(Champs["Date"], Champs["Other_spells"], 'y.-', label='Other spells')
axis[1,1].set(xlabel='Other spells',ylabel='Count')

plt.show()

# %% [markdown]
# The surprising value of 15 Lands in the first winnign deck can be explained by the fact that it was playing Moxes, artifacts (hence, Other spells) which provide one mana of a certain color. We also observe two peaks in the Other spells count in years 2000 and 2020. 2000 was the year of the Tinker deck - mainly based on the Sorcery 'Tinker' and a great amount of artifacts.
# 
# Then we use violin plots to visualise the distribution of the four groups.

# %%
figure, axis = plt.subplots(2, 2, figsize=(12,8)) 

sns.violinplot(x='Rank', y='Lands', data=data, fill=False, inner='quart', ax=axis[0,0])
sns.stripplot(x='Rank', y='Lands', data=data, alpha=0.3, color='navy', jitter=0.05, ax=axis[0,0])
axis[0,0].set(xlabel='Rank',ylabel='Lands')
sns.violinplot(x='Rank', y='Creatures', data=data, fill=False, inner='quart', ax=axis[1,0])
sns.stripplot(x='Rank', y='Creatures', data=data, alpha=0.3, color='navy', jitter=0.05, ax=axis[1,0])
axis[1,0].set(xlabel='Rank',ylabel='Creatures')
sns.violinplot(x='Rank', y='Instants_Sorceries', data=data, fill=False, inner='quart', ax=axis[0,1])
sns.stripplot(x='Rank', y='Instants_Sorceries', data=data, alpha=0.3, color='navy', jitter=0.05, ax=axis[0,1])
axis[0,1].set(xlabel='Rank',ylabel='Instants & Sorceries')
sns.violinplot(x='Rank', y='Other_spells', data=data, fill=False, inner='quart', ax=axis[1,1])
sns.stripplot(x='Rank', y='Other_spells', data=data, alpha=0.3, color='navy', jitter=0.05, ax=axis[1,1])
axis[1,1].set(xlabel='Rank',ylabel='Other spells')

plt.show()

# %% [markdown]
# Apparently, there is no difference, on average, in the composition of the decks. A box plot can confirm this claim, by also giving a more reasonable output (we cannot expect a negative number of cards in a deck).

# %%
figure, axis = plt.subplots(2, 2, figsize=(12,8)) 

sns.boxplot(x='Rank', y='Lands', data=data, ax=axis[0,0])
axis[0,0].set(xlabel='Rank',ylabel='Lands')
sns.boxplot(x='Rank', y='Creatures', data=data, ax=axis[1,0])
axis[1,0].set(xlabel='Rank',ylabel='Creatures')
sns.boxplot(x='Rank', y='Instants_Sorceries', data=data, ax=axis[0,1])
axis[0,1].set(xlabel='Rank',ylabel='Instants & Sorceries')
sns.boxplot(x='Rank', y='Other_spells', data=data, ax=axis[1,1])
axis[1,1].set(xlabel='Rank',ylabel='Other spells')

plt.show()

# %% [markdown]
# ## Statistical tests for equality of the means
# 
# To begin with, we want to determine whether there is a statistically significant difference between the number of Lands in decks that ranked first, second, third or fourth, on average.
# 
# We have two ways to perform this. The first one is to divide the data on the number of Lands into four groups corresponding to the four rankings and pass them to an **ANOVA test**. In its simplest form, ANOVA provides a statistical test of whether two or more population means are equal, and therefore generalizes the t-test beyond two means. In other words, the ANOVA is used to test the difference between two or more means.
# 
# However, the analysis of variance can be presented in terms of a linear model, which makes the following assumptions about the probability distribution of the responses:
# 
# - Independence of observations : this is an assumption of the model that simplifies the statistical analysis.
# - Normality : the distributions of the residuals are normal. In our case, the distribution of the data in each group.
# - Equality (or "homogeneity") of variances, called homoscedasticity : the variance of data in groups should be the same.
# 
# The second way is to repeatedly use **Welch's t-test**, which allows to compare means of populations with different variances, but the assumption of normality is maintained.
# 
# In each case, we need to divide the data of interest into 4 different groups according to the ranking. Let us perform this.

# %%
Lands_groups = []
for i in range(4) :
    Lands_groups.append(data[data['Rank'] == (i+1)]['Lands'])

Creature_groups = []
for i in range(4) :
    Creature_groups.append(data[data['Rank'] == (i+1)]['Creatures'])

IandS_groups = []
for i in range(4) :
    IandS_groups.append(data[data['Rank'] == (i+1)]['Instants_Sorceries'])

Others_groups = []
for i in range(4) :
    Others_groups.append(data[data['Rank'] == (i+1)]['Other_spells'])

# %% [markdown]
# Then let us check the homoscedasticity assumption by printing a table of variances:

# %%
data[['Rank','Creatures','Instants_Sorceries','Other_spells','Lands']].groupby('Rank',observed=False).apply(np.var, (0))

# %% [markdown]
# Therefore we cannot rely on homoscedasticity, but we may still perform the ANOVA test, for the sake of seeing the outcomes.

# %%
long_data = pd.melt(frame=data,
                    id_vars=['Deck','Player','Event','Rank','Date'],
                    value_vars=['Creatures','Instants_Sorceries','Other_spells','Lands'],
                    var_name='Type',
                    value_name='Count')

for name_group in long_data.groupby('Type',observed=False):
    samples = [condition[1] for condition in name_group[1].groupby('Rank',observed=False)['Count']]
    f_val, p_val = ss.f_oneway(*samples)
    print(f'Type: {name_group[0]},\nF value: {f_val:.3f},\np value: {p_val:.3f}\n')

# %% [markdown]
# Thus, apparently, there is no significant difference. We could apply a t-test to confirm the conclusion, but there is an additional issue to address: in general, data are not normally distributed.

# %%
for name_group in long_data.groupby(by=['Type','Rank'], observed=False):
    samples = [condition for condition in name_group[1]['Count']]
    w_val, p_val = ss.shapiro(samples)
    print(f'Type: {name_group[0][0]},\nRank: {name_group[0][1]}\nW value: {w_val:.3f},\np value: {p_val:.3f}\n')

# %% [markdown]
# The following frequency plot confirms what we already observed.

# %%
figure, axis = plt.subplots(4,4, figsize=(12,12)) 

for i,group in enumerate([Lands_groups,Creature_groups,IandS_groups,Others_groups]) :
    for j in range(4) :
        axis[i,j].hist(group[j], density=True)
        mu, std = ss.norm.fit(group[j]) 
        xmin, xmax = axis[i,j].get_xlim()
        x = np.linspace(xmin, xmax, 100)
        p = ss.norm.pdf(x, mu, std)
        axis[i,j].plot(x, p, 'k', linewidth=2)
        axis[i,j].get_yaxis().set_ticks([])

axis[0,0].set(ylabel='Lands', title='Rank 1')
axis[0,1].set(title='Rank 2')
axis[0,2].set(title='Rank 3')
axis[0,3].set(title='Rank 4')
axis[1,0].set(ylabel='Creatures')
axis[2,0].set(ylabel='Instants & Sorceries')
axis[3,0].set(ylabel='Others')

plt.show()

# %% [markdown]
# This might be due to a low number of observations or to a trend we cannot identify at present. Nevertheless, we expect our data to be normally distributed (possibly with unequal variances) and thus we apply Welch's t-test as discussed.

# %%
for i,group in enumerate([Creature_groups,IandS_groups,Others_groups,Lands_groups]) :
    for j in range(4) :
        if i != j :
            t_val, p_val = ss.ttest_ind(group[i], group[j], equal_var = False)
            print(f'Type : {data.columns[i+5]}\nRank {i+1} vs Rank {j+1}\nT statistic : {t_val:.3f}\np value : {p_val:.3f}\n')

# %% [markdown]
# ## Conclusions
# 
# We conclude that there is no statistically significant difference at level alpha = 0.05 in the composition of the decks. The conclusion does not change if we consider the double-faced cards Land/non-Land as Lands. A further analysis may take into account colors or frequency of single cards in a deck.

# %% [markdown]
# ## Appendix
# 
# It could be interesting to see how the number of Lands, Creatures, Instants & Sorceries, and Other spells evolved in time for all rankings (and not just the top one).

# %%
g = sns.relplot(kind='line', 
                data=data, 
                x='Date', 
                y='Lands', 
                hue='Rank', 
                col='Rank', 
                col_wrap=2, 
                legend = False).set_axis_labels("Year", "Lands")

# %%
g = sns.relplot(kind='line', 
                data=data, 
                x='Date', 
                y='Creatures', 
                hue='Rank', 
                col='Rank', 
                col_wrap=2, 
                legend = False).set_axis_labels("Year", "Creatures")

# %%
g = sns.relplot(kind='line', 
                data=data, 
                x='Date', 
                y='Instants_Sorceries', 
                hue='Rank', 
                col='Rank', 
                col_wrap=2, 
                legend = False).set_axis_labels("Year", "Instants & Sorceries")

# %%
g = sns.relplot(kind='line', 
                data=data, 
                x='Date', 
                y='Other_spells', 
                hue='Rank', 
                col='Rank', 
                col_wrap=2, 
                legend = False).set_axis_labels("Year", "Others")


