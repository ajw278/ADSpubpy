import requests
from pylatex import Document, Command, NewLine, NoEscape
import re

from datetime import datetime

# Replace with your NASA/ADS API key
API_KEY = None
library_id = 'PK0RWOWOTIKWfo-5Fck9sg'  # Replace with your actual library ID

journal_short = {'Monthly Notices of the Royal Astronomical Society': 'MNRAS', 'The Astrophysical Journal': 'ApJ', 'Astronomy & Astrophysics': 'A\&A', 'European Physical Journal Plus': 'EPJ+', 'Nature': 'Nature', 'The Astronomical Journal': 'AJ'}


accept_journals = ['MNRAS', 'ApJ', 'A\&A','EPJ+', 'Nature','AJ', 'arXiv e-prints']

# Function to fetch publications from NASA/ADS API
def fetch_publications(library_id):
    url = f'https://api.adsabs.harvard.edu/v1/biblib/libraries/{library_id}?start=0&rows=200'

    headers = {
        'Authorization': f'Bearer {API_KEY}'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    library_data = response.json()
    
    # Fetch the list of bibcodes
    bibcodes = library_data['documents']
    
    # Fetch publication details for each bibcode
    publications = []
    for bibcode in bibcodes:
        pub_url = f'https://api.adsabs.harvard.edu/v1/search/query?q=bibcode:{bibcode}&fl=title,author,pub,reference,year,volume,page_range,page,doi,pubdate,citation_count,author_count'
        pub_response = requests.get(pub_url, headers=headers)
        pub_response.raise_for_status()
        pub_data = pub_response.json()
        
        
        if pub_data['response']['docs']:
            pub_info = pub_data['response']['docs'][0]
            title = pub_info.get('title', [''])[0]
            authors = pub_info.get('author', [])
            journal = pub_info.get('pub', [''])
            if journal in journal_short:
                 journal = journal_short[journal]
            reference = pub_info.get('reference', [''])
            volume =  pub_info.get('volume', [''])
            page =  pub_info.get('page_range', '')
            if page=='':
                 page= pub_info.get('page', '')[0]
            doi = pub_info.get('doi', [''])[0]
            year = pub_info.get('year', '')
            date = pub_info.get('pubdate', '')
            citations = pub_info.get('citation_count', 0)
            nauthors = pub_info.get('author_count', 0)
            # Combine year and month into a single date string
            
            if date!='':
                 date = reformat_date(date)

            publications.append({
                'title': title,
                'authors': authors,
                'journal': journal,
                'date': date,
                'citations': str(citations),
                'doi': doi, 
                'volume': volume, 
                'page_range': page,
                'author_count':nauthors
            })
    return publications
    
def reformat_date(date_str):
    # Check if the date_str is valid and contains the month part
    try:
        date = datetime.strptime(date_str[:7], '%Y-%m')
        formatted_date = date.strftime('%b %y')  # Format: Mon YY
        return formatted_date
    except ValueError:
        return "Invalid date"

# Function to reformat author names
def reformat_authors(authors, nauthors, nauthmax=3):
    reformatted_authors = []
    for iauth, author in enumerate(authors):
        if iauth>=nauthmax or iauth>=nauthors:
              break
        last, first = author.split(',', 1)
        first_names = first.strip().split()
        initials = ' '.join([name[0] + '.' for name in first_names])
        reformatted_authors.append(f"{initials} {last.strip()}")
    
    if nauthors>nauthmax:
          reformatted_authors.append(r'\textit{et al.}')
    return reformatted_authors

# Function to generate LaTeX document
def generate_latex(publications):
    doc = Document()
    
    # Add the custom LaTeX preamble
    doc.preamble.append(NoEscape(r'\documentclass[12pt,a4paper]{moderncv}'))
    doc.preamble.append(NoEscape(r'\moderncvtheme[blue]{classic}'))
    doc.preamble.append(NoEscape(r'\usepackage[utf8]{inputenc}'))
    doc.preamble.append(NoEscape(r'\usepackage[top=2.5cm, bottom=2.5cm, left=2.5cm, right=2.5cm]{geometry}'))
    doc.preamble.append(NoEscape(r'\usepackage{graphicx}'))
    doc.preamble.append(NoEscape(r'\firstname{Andrew}'))
    doc.preamble.append(NoEscape(r'\familyname{Winter}'))
    doc.preamble.append(NoEscape(r'\title{\small{Publication list -- \today } \vspace{-2ex}}'))
    doc.preamble.append(NoEscape(r'\address{Observatoire de la C\^{o}te d\'Azur\\96 Bd de l\'Observatoire\\06300 Nice, France\\}'))
    doc.preamble.append(NoEscape(r'\email{\,andrew.winter@oca.eu}'))
    doc.preamble.append(NoEscape(r'\makeatletter'))
    doc.preamble.append(NoEscape(r'\renewcommand*{\bibliographyitemlabel}{\@biblabel{\arabic{enumiv}}}'))
    doc.preamble.append(NoEscape(r'\makeatother'))
    doc.preamble.append(NoEscape(r'\usepackage{multibib}'))
    doc.preamble.append(NoEscape(r'\newcites{book,misc}{{Books},{Others}}'))
    doc.preamble.append(NoEscape(r'\nopagenumbers{}'))
    doc.preamble.append(NoEscape(r'\begin{document}'))
    doc.preamble.append(NoEscape(r'\maketitle'))
    doc.preamble.append(NoEscape(r'\vspace{-9ex}'))
    
    # Add FIRST AUTHOR PUBLICATIONS
    doc.append(NoEscape(r'\textbf{FIRST AUTHOR PUBLICATIONS:}'))
    doc.append(NewLine())
    doc.append(NewLine())
    
    for pub in publications:
        first_author = pub['authors'][0] if pub['authors'] else ''
        nauthors = pub['author_count']
        if re.match(r'^Winter, (Andrew J?\.?|A\. J\.)', first_author, re.IGNORECASE):
            # Reformat authors and ensure your name appears correctly
            formatted_authors = reformat_authors(pub['authors'][:3], nauthors)
            myname = formatted_authors[0]
            formatted_authors[0] = r'\textbf{'+myname+'}'
            if nauthors==2:
                 authors_formatted = ' \& '.join(formatted_authors)
            else:
                 authors_formatted = ', '.join(formatted_authors)
            journal = pub['journal']
            if journal=='arXiv e-prints':
            	ref = pub['doi']
            elif journal in accept_journals:
                if pub['page_range']=='':
                     pr = ''
                else:
                     pr = ':' +pub['page_range']
                ref = journal + r' \textbf{' +str(pub['volume'])+r'}'+pr
            
            if journal in accept_journals:
            	doc.append(Command('cventry', [  pub['date'],
            	     NoEscape(r'\textnormal{\textit{' + pub['title'] + ' -- Citations: ' + pub['citations'] + '\n' + r'} \newline ' + authors_formatted + ' -- ' + ref +'}}{}{}{}{')]))
            	doc.append(NoEscape(''))
            else:
                print('REJECTED:', pub['title'], journal)
        
    doc.append(NoEscape(r'\textbf{OTHER PUBLICATIONS:}'))
    doc.append(NewLine())
    doc.append(NewLine())    	
    for pub in publications:
        first_author = pub['authors'][0] if pub['authors'] else ''
        nauthors = pub['author_count']
        if not re.match(r'^Winter, (Andrew J?\.?|A\. J\.)', first_author, re.IGNORECASE):
            # Reformat authors and ensure your name appears correctly
            formatted_authors = reformat_authors(pub['authors'][:3], nauthors)
            
            me_first = False
            for iauth, auth in enumerate(pub['authors'][:3]):
                  if re.match(r'^Winter, (Andrew J?\.?|A\. J\.)', auth, re.IGNORECASE):
                        me_first=True
                        myname = formatted_authors[iauth]
                        formatted_authors[iauth] = r'\textbf{'+myname+'}'
            
            if not me_first:
                    formatted_authors = formatted_authors[:2]
                    formatted_authors.append(r'\dots \textbf{A. J. Winter} \textit{et al.}')
                  
            
            if nauthors==2:
                 authors_formatted = ' \& '.join(formatted_authors)
            else:
                 authors_formatted = ', '.join(formatted_authors)
            
            journal = pub['journal']
            if journal=='arXiv e-prints':
            	ref = pub['doi']
            elif journal in accept_journals:
            	ref = journal + r' \textbf{' +str(pub['volume'])+r'}:'+str(pub['page_range'])
            
            if journal in accept_journals:
            	doc.append(Command('cventry', [  pub['date'],
            	     NoEscape(r'\textnormal{\textit{' + pub['title'] + ' -- Citations: ' + pub['citations'] + r'} \newline ' + authors_formatted + ' -- ' + ref +'}}{}{}{}{')]))
            else:
                print('REJECTED:', pub['title'], journal)
    return doc

if__name__=='__main__':
	publications = fetch_publications(library_id)
	latex_doc = generate_latex(publications)
	latex_doc.generate_pdf('publications', clean_tex=False)
