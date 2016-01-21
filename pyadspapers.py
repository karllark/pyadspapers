#!/usr/bin/env python
#
# Code created to help me learn python as well as fully automate
# the creation of HTML pages for all my papers and index pages
# with various sorts.  This used to be done with IDL code and a by
# hand created flat ASCII "database" file.
#
# The code queries ADS for to get the list of bibcodes for one author.
# Then it grabs the information for each paper, generates an HTML
# page for each paper, and an set of index pages with different sorts.
# Plots are even generated (new for the python version).
#
# Use at your own risk.  I wrote this for my personal use and to learn
# python.  I image it will immediately break if you try and use it.
# And that there are much more efficient ways to impliment this code.
# But, I'd be happy to hear from you if you find it useful and/or
# improve the code.
#
# Written: 2010-2012 (at least that is my guess)
# Initital version finished: 19 Oct 2012 (Karl D. Gordon: kgordon@stsci.edu,
#      in a hotel room in Belgium)
#  2013-2015 : updates to improve funtionality and make prettier plots
#  Jan 2016  : updates stareted to be compatible with python 3 and PEP8
# 
import urllib
import sys
if sys.version_info >= (3, 0):
    from html.parser import HTMLParser
else:
    from HTMLParser import HTMLParser
import xml.etree.cElementTree as ET
import math
import pylab as p
from operator import itemgetter, attrgetter
import string
import pickle
#from pytagcloud import create_tag_image, make_tags
#from pytagcloud.lang.counter import get_tag_counts

# Objext for a single paper
class Paper:
    def __init__(self, bibcode, get_citations):
        self.bibinfo = {}

        # get the ADS entry and determine the basic info on this paper
        data = ET.parse(urllib.urlopen("http://adsabs.harvard.edu/abs/" +
                                       bibcode + "&data_type=XML"))
        root = data.getroot()

        a = root.getchildren()
        alltags = a[0].getchildren()

        self.num_cites = 0
        self.bibinfo['volume'] = '1'
        self.author_rank = 0
        
        for curtag in alltags:
            z = len(curtag.tag)
            subtag = curtag.tag[49:z]
            if subtag == "bibcode":
                self.bibcode = curtag.text
            elif subtag == "title":
                self.bibinfo['title'] = curtag.text
            elif subtag == "abstract":
                self.bibinfo['abstract'] = curtag.text
            elif subtag == "pubdate":
                self.bibinfo['date'] = curtag.text[4:8]
            elif subtag == "journal":
                self.bibinfo['journal'] = curtag.text
            elif subtag == "volume":
                self.bibinfo['volume'] = curtag.text
            elif subtag == "page":
                self.bibinfo['page'] = curtag.text
            elif subtag == "lastpage":
                self.bibinfo['lastpage'] = curtag.text
            elif subtag == "author":
                if 'authors' in self.bibinfo:
                    self.bibinfo['authors'].append(curtag.text)
                else:
                    self.bibinfo['authors'] = [curtag.text]
                if not string.find(curtag.text,'Gordon'):
                    self.author_rank = len(self.bibinfo['authors'])
            elif subtag == "citations":
                self.num_cites = int(curtag.text)

        self.ave_cites_per_year = 0.
        self.n_years = 0
        if (get_citations != 0) and (self.num_cites > 0):

            self.num_self_cites = 0
            self.num_cites_year = {}
            self.num_self_cites_year = {}

            amp_sym = bibcode.find('&')
            if (amp_sym > 0):
                bibcode = bibcode[0:amp_sym] + '%26' + \
                          bibcode[amp_sym+1:len(bibcode)]
            # now get the number of citations per year
            data = ET.parse(urllib.urlopen('http://adsabs.harvard.edu/cgi-bin/' +
                                           'nph-ref_history?bibcode=' +
                                           bibcode.encode('utf-8') +
                                           "&refs=CITATIONS&data_type=XML"))
            root = data.getroot()
            cites = root.getchildren()

            # need this variable to be able to sort, probably shouldn't use a
            #   dictionary, but I did to start
            for v in cites:
                a = v.attrib
                self.num_cites_year[a["year"]] = int(a["total"])
                self.ave_cites_per_year += float(a["total"])
                self.n_years += 1

            self.ave_cites_per_year /= self.n_years

    def WriteHtml(self):

        # open the file for writing
        out_file = open(self.bibcode+'.html', 'w')
        
        out_file.write('<?xml version="1.0" encoding="utf-8" ?>\n')
        out_file.write('<!DOCTYPE html\n')
        out_file.write('  PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"\n')
        out_file.write('     "DTD/xhtml1-transitional.dtd">\n')
        out_file.write('\n')
        out_file.write('<html xmlns="http://www.w3.org/1999/xhtml" ' +
                       'xml:lang="en" lang="en">\n')
        out_file.write('<head>\n')
        out_file.write('<link rel="stylesheet" type="text/css" ' +
                       'href="../kgmain.css" />')
        out_file.write('<title>\n')
        out_file.write(self.bibinfo['title'].encode('utf-8')+'\n')
        #out_file.write(self.bibinfo['title']+'\n')
        out_file.write('</title>\n')
        out_file.write('</head>\n')
        
        out_file.write('<body>\n')
        
        out_file.write('<h1 align="center">\n')
        out_file.write(self.bibinfo['title'].encode('utf-8')+'</h1>\n')
        out_file.write('<h3 align="center">\n')
        for i in range(len(self.bibinfo['authors'])-1):
            out_file.write(self.bibinfo['authors'][i].encode('utf-8')+', ')
        out_file.write('&amp; '+self.bibinfo['authors']\
                       [len(self.bibinfo['authors'])-1].encode('utf-8')+'<br />')
        comma_loc = self.bibinfo['journal'].find(',')
        shortjournal = self.bibinfo['journal'][0:comma_loc]
        out_file.write(self.bibinfo['date'].encode('utf-8') + ', ' +
                       shortjournal.encode('utf-8') + ', ' +
                       self.bibinfo['volume'].encode('utf-8') + ', ' +
                       self.bibinfo['page'].encode('utf-8'))
        out_file.write('</h3>\n')

        out_file.write('\n')
        out_file.write('<hr />\n')
        out_file.write('<p>')
        out_file.write(self.bibinfo['abstract'].encode('utf-8'))
        out_file.write('</p>')
        out_file.write('\n')
        
        out_file.write('<p>')
        out_file.write('[<a href="http://adsabs.harvard.edu/abs/' +
                       self.bibcode + '">ADS</a>]')
        out_file.write('</p>')

        out_file.write('<p>')
        out_file.write('<a href="http://adsabs.harvard.edu/cgi-bin/' +
                       'nph-ref_query?bibcode='+self.bibcode+
                       '&amp;refs=CITATIONS&amp;db_key=AST">ADS Citation Query' +
                       '</a><br />\n')
        if self.num_cites > 0:
            out_file.write('# citations = '+repr(self.num_cites)+'<br />\n')

            out_file.write('citations vs. year [year,citations]<br />\n')
            ckeys = self.num_cites_year.keys()
            ckeys.sort()
            x = []
            y = []
            for k in ckeys:
                out_file.write('['+k+','+repr(self.num_cites_year[k])+']')
                x.append(k)
                y.append(self.num_cites_year[k])

            out_file.write('\n')

            # create the plot of the citations per year
            fig = p.figure()
            ax = fig.add_subplot(1,1,1)

            ind = range(len(y))
            ax.bar(ind, y, facecolor='#777777', ecolor='black', align='center')
            ax.set_ylabel('Citations')
            ax.set_title(self.bibcode,fontstyle='italic')
            ax.set_xticks(ind)
            ax.set_xticklabels(x)
            fig.autofmt_xdate()

            cite_plot_file = self.bibcode+'_cites_per_year.png'
            p.savefig(cite_plot_file, dpi=50, bbox_inches='tight',
                      pad_inches=0.25)
            p.close()

            # insert the plot in the html file
            out_file.write('<br />\n')
            out_file.write('<img align="left" alt="Citations by year" src="'+
                           cite_plot_file+'" /><br clear="left" />\n')

            out_file.write('</p>')

        out_file.write('\n')
        out_file.write('<hr />\n')
        out_file.write('<p>\n')
        out_file.write('Copyright &copy; 2012\n')
        out_file.write('<a href="http://www.stsci.edu/~kgordon/kgordon.html">' +
                       'Karl D. Gordon</a>\n')
        out_file.write('All Rights Reserved\n')
        out_file.write('</p>\n')
        
        out_file.write('</body>\n')
        out_file.write('</html>\n')

    def __repr__(self):
        return "Paper(" + self.bibcode + ")"

# Parser for HTML pages from ADS
class MyADSPapersParser(HTMLParser):
    def __init__(self):
        self.reset()
        self.bibcodes = [];

    def handle_starttag(self, tag, attrs):
        if tag == 'input' and attrs:
            if (attrs[1][1] == 'bibcode') and (attrs[2][1][0:3] != 'ads'):
                self.bibcodes.append(attrs[2][1])

# Object for the bibcodes of a list of papers
class Papers:
    def __init__(self, lastname, firstinital, min_year):
        
        # get the ADS entry and determine the basic info on this paper
        f = urllib.urlopen("http://adsabs.harvard.edu/cgi-bin/nph-abs_connect?db_key=AST&amp;sim_query=YES&amp;aut_xct=NO&amp;aut_logic=OR&amp;obj_logic=OR&amp;author="+lastname+"%2C+"+firstinital+"+&amp;object=&amp;start_mon=&amp;start_year="+min_year+"&amp;end_mon=&amp;end_year=&amp;ttl_logic=OR&amp;title=&amp;txt_logic=OR&amp;text=&amp;nr_to_return=1000&amp;start_nr=1&amp;start_entry_day=&amp;start_entry_mon=&amp;start_entry_year=&amp;min_score=&amp;jou_pick=NO&amp;ref_stems=&amp;data_and=ALL&amp;group_and=ALL&amp;sort=SCORE&amp;aut_syn=YES&amp;ttl_syn=YES&amp;txt_syn=YES&amp;aut_wt=1.0&amp;obj_wt=1.0&amp;ttl_wt=0.3&amp;txt_wt=3.0&amp;aut_wgt=YES&amp;obj_wgt=YES&amp;ttl_wgt=YES&amp;txt_wgt=YES&amp;ttl_sco=YES&amp;txt_sco=YES&amp;version=1")
        self.ads_page = f.read()
        f.close()

        p = MyADSPapersParser()
        p.feed(self.ads_page)
        p.close()

        self.bibcodes = p.bibcodes

    def __repr__(self):
        return "Papers(" + self.bibcodes + ")"


# Object for multiple Paper objects
class lotsofpapers:
    def __init__(self):
        self.papers = []

    def WriteHtml(self, lastname, firstinital, sorttype):

        max_papers = len(self.papers)

        # get the values for sorting
        vals = []
        for i in range(max_papers):
            if sorttype == "date":
                cur_val = (i,self.papers[i].bibinfo['date'])
            elif sorttype == "cites":
                if self.papers[i].num_cites == 0:
                    cur_val = (i,0.0)
                else:
                    cur_val = (i,math.log10(self.papers[i].num_cites))
            elif sorttype == "cites_per_year":
                if self.papers[i].ave_cites_per_year == 0:
                    cur_val = (i,0.0)
                else:
                    cur_val = (i,math.log10(self.papers[i].ave_cites_per_year))
            elif sorttype == "author_rank":
                cur_val = (i,self.papers[i].author_rank)
            elif sorttype == "n_authors":
                cur_val = (i,math.log10(len(self.papers[i].bibinfo['authors'])))
                
            vals.append(cur_val)

        # some defaults for the output
        mult_val = 1
        log_bins = 0
        if sorttype == "date":
            delta_test_val = 0
            sorttype_str = "Date"
        elif sorttype == "cites":
            log_bins = 1
            delta_test_val = 0.2
            sorttype_str = "Citations"
        elif sorttype == "cites_per_year":
            log_bins = 1
            delta_test_val = 0.2
            sorttype_str = "Citations per year"
        elif sorttype == "author_rank":
            delta_test_val = 0
            mult_val = -1
            sorttype_str = "Author Rank"
        elif sorttype == "n_authors":
            log_bins = 1
            delta_test_val = 0.1
            mult_val = -1
            sorttype_str = "Number of Authors"

        # sort the values
        reverse_val = True
        if mult_val == -1:
            reverse_val = False
        vals_sorted = sorted(vals,key=itemgetter(1), reverse=reverse_val)

        # make the summary plot
        if delta_test_val == 0:
            vals_for_hist = [float(x[1]) for x in vals]
        else:
            vals_for_hist = [float(x[1])//delta_test_val for x in vals]

        fig = p.figure(figsize=(15,5))
        ax = fig.add_subplot(1,1,1)

        n_hpts = int(max(vals_for_hist) - min(vals_for_hist)) + 1
        ind = range(n_hpts)
        ind = [x + int(min(vals_for_hist)) for x in ind]
        ind_half = [x - 0.5 for x in ind]
        ind_half.append(max(ind) + 0.5)
        if delta_test_val == 0:
            ind_str = [repr(x) for x in ind]
        else:
            ind_str = ["{0:.0f}".format(math.pow(10,x*delta_test_val))+
                       '-'+"{0:.0f}".format(math.pow(10,(x+1)*delta_test_val))
                       for x in ind]
            if ind_str[0] == '1-2':
                ind_str[0] = '0-2'

        bins = ax.hist(vals_for_hist, color='#777777', bins=ind_half,
                       rwidth=0.75, align='mid')

        ax.set_ylim(top=max(bins[0]) + 0.1)

#        ax.set_xlim(left=min(vals_for_hist)

        ax.set_ylabel('Number')
        ax.set_title(sorttype_str,fontstyle='italic')
        ax.set_xticks(ind)
        ax.set_xticklabels(ind_str)
        fig.autofmt_xdate()

#        p.show()
        basename = lastname + firstinital
        plot_file = basename+sorttype+'.png'
        p.savefig(plot_file, dpi=50, bbox_inches='tight', pad_inches=0.25)
        p.close()

        # open the file for writing
        out_file = open(basename+'_'+sorttype+'.html', 'w')
        # include a latex version of CV fun
        out_file_tex_all = open(basename+'_'+sorttype+'.tex', 'w')
        if sorttype == "date":
            out_file_tex_1st = open(basename+'_'+sorttype+'_1st.tex', 'w')
        # output an ascii file useful for importing into other places
        out_file_ascii = open(basename+'_'+sorttype+'.txt', 'w')
        
        out_file.write('<?xml version="1.0" encoding="utf-8" ?>\n')
        out_file.write('<!DOCTYPE html\n')
        out_file.write('  PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"\n')
        out_file.write('     "DTD/xhtml1-transitional.dtd">\n')
        out_file.write('\n')
        out_file.write('<html xmlns="http://www.w3.org/1999/xhtml" ' +
                       'xml:lang="en" lang="en">\n')
        out_file.write('<head>\n')
        out_file.write('<link rel="stylesheet" type="text/css" ' +
                       'href="../kgmain.css" />')
        out_file.write('<title>\n')
        out_file.write(firstinital + ' ' + lastname+"'s Refereed Journal Papers")
        
        out_file.write('</title>\n')
        out_file.write('</head>\n')
        
        out_file.write('<body>\n')
        
        out_file.write('<h1 align="center">\n')
        out_file.write(firstinital+' '+lastname+
                       "'s Refereed Journal Papers<br />\n")
        out_file.write('Sorted by ' + sorttype_str + '\n')
        out_file.write('</h1>\n')
        
        out_file.write('\n')

        out_file.write('<p>\n')
        out_file.write('Sorted by <a href="'+basename+'_date.html">Date</a>,\n')
        out_file.write('<a href="'+basename+
                       '_author_rank.html">Author Rank</a>,\n')
        out_file.write('<a href="'+basename+
                       '_n_authors.html">Number of Authors</a>,\n')
        out_file.write('<a href="'+basename+
                       '_cites.html">Number of Citations</a>,\n')
        out_file.write('<a href="'+basename+
                       '_cites_per_year.html">Number of Citations/Year</a>\n')
        out_file.write('<br />\n')
        out_file.write('Other Sources ==>\n')
        out_file.write('[<a href="http://adsabs.harvard.edu/cgi-bin/nph-abs_connect?db_key=AST&amp;sim_query=YES&amp;aut_xct=NO&amp;aut_logic=OR&amp;obj_logic=OR&amp;author=gordon%2C+k+&amp;object=&amp;start_mon=&amp;start_year=1992&amp;end_mon=&amp;end_year=&amp;ttl_logic=OR&amp;title=&amp;txt_logic=OR&amp;text=&amp;nr_to_return=1000&amp;start_nr=1&amp;start_entry_day=&amp;start_entry_mon=&amp;start_entry_year=&amp;min_score=&amp;jou_pick=NO&amp;ref_stems=&amp;data_and=ALL&amp;group_and=ALL&amp;sort=SCORE&amp;aut_syn=YES&amp;ttl_syn=YES&amp;txt_syn=YES&amp;aut_wt=1.0&amp;obj_wt=1.0&amp;ttl_wt=0.3&amp;txt_wt=3.0&amp;aut_wgt=YES&amp;obj_wgt=YES&amp;ttl_wgt=YES&amp;txt_wgt=YES&amp;ttl_sco=YES&amp;txt_sco=YES&amp;version=1">ADS Refereed Publications Search</a>]\n')
        out_file.write('[<a href="http://adsabs.harvard.edu/cgi-bin/nph-abs_connect?db_key=AST&amp;sim_query=YES&amp;aut_xct=NO&amp;aut_logic=OR&amp;obj_logic=OR&amp;author=gordon%2C+k&amp;object=&amp;start_mon=&amp;start_year=1992&amp;end_mon=&amp;end_year=&amp;ttl_logic=OR&amp;title=&amp;txt_logic=OR&amp;text=&amp;nr_to_return=1000&amp;start_nr=1&amp;start_entry_day=&amp;start_entry_mon=&amp;start_entry_year=&amp;min_score=&amp;jou_pick=EXCL&amp;ref_stems=&amp;data_and=ALL&amp;group_and=ALL&amp;sort=SCORE&amp;aut_syn=YES&amp;ttl_syn=YES&amp;txt_syn=YES&amp;aut_wt=1.0&amp;obj_wt=1.0&amp;ttl_wt=0.3&amp;txt_wt=3.0&amp;aut_wgt=YES&amp;obj_wgt=YES&amp;ttl_wgt=YES&amp;txt_wgt=YES&amp;ttl_sco=YES&amp;txt_sco=YES&amp;version=1">ADS Non-refereed Publications Search</a>]\n')
        out_file.write('[<a href="http://arxiv.org/find/astro-ph/1/au:+Gordon_K/0/1/0/all/0/1">arXiv.org e-Print (astro-ph)</a>]\n')
        out_file.write('</p>\n')

        out_file.write('<hr />\n')
        out_file.write('<p>\n')
        out_file.write('<img src="'+plot_file+'" alt="plot of '+
                       sorttype_str+'" />\n')
        out_file.write('</p>\n')
        
        test_val_prev = 0

        for l in range(max_papers):
            i = vals_sorted[l][0]

            out_file.write('\n')

            if sorttype == "date":
                test_val = vals_sorted[l][1]
            elif sorttype == "cites":
                test_val = vals_sorted[l][1]//delta_test_val
            elif sorttype == "cites_per_year":
                test_val = vals_sorted[l][1]//delta_test_val
            elif sorttype == "author_rank":
                test_val = repr(vals_sorted[l][1])
            elif sorttype == "n_authors":
                test_val = vals_sorted[l][1]//delta_test_val

            if (l == 0) or (mult_val*(float(test_val_prev) - float(test_val))
                            >= 1): 
                out_file.write('<hr />\n')
                if (delta_test_val > 0):
                    if log_bins:
                        if test_val == 0.0:
                            out_file.write('<h3>'+"{0:.0f}".format(0.0) + '-' +
                                           "{0:.0f}".format(math.pow(10,delta_test_val))+'</h3>\n')
                        else:
                            out_file.write('<h3>'+"{0:.0f}".format(math.pow(10,test_val*delta_test_val))+
                                           '-'+"{0:.0f}".format(math.pow(10,(test_val+1)*delta_test_val))+'</h3>\n')
                    else:
                        out_file.write('<h3>'+repr(test_val*delta_test_val)+
                                       '-'+repr((test_val+1)*delta_test_val)+
                                       '</h3>\n')
                else:
                    out_file.write('<h3>'+test_val+'</h3>\n')
                out_file.write('\n')
                test_val_prev = test_val

            out_file.write('<p>')
            if sorttype == "cites":
                out_file.write('# cites = ' + repr(self.papers[i].num_cites) +
                               '<br />\n')
            elif sorttype == "cites_per_year":
                out_file.write('ave. cites/year = ' +
                        "{0:.2f}".format(self.papers[i].ave_cites_per_year) +
                               '<br />\n')

            out_file.write(str(max_papers-i))
            out_file.write('.\n')
            out_file.write('<a href="'+self.papers[i].bibcode+'.html">\n')
            out_file.write(self.papers[i].bibinfo['title'].encode('utf-8')+'\n')
            out_file.write('</a><br />\n')

            if sorttype == "date":
                if self.papers[i].bibinfo['authors'][0][:6] == 'Gordon':
                    out_file_tex = out_file_tex_1st
                else:
                    out_file_tex = out_file_tex_all
            else:
                out_file_tex = out_file_tex_all

            out_file_tex.write('\item ')
            out_file_tex.write(self.papers[i].bibinfo['title'].encode('utf-8')+
                               ' \\\\ \n')
            
            out_file_ascii.write(self.papers[i].bibinfo['title'].encode('utf-8')+
                                 '\n')

            n_authors = len(self.papers[i].bibinfo['authors'])
            max_authors = n_authors
            if (n_authors > 5): max_authors = 5

            authname = self.papers[i].bibinfo['authors'][0].encode('utf-8')
            out_file.write(authname)
            out_file_tex.write(authname)
            for k in range(1,max_authors-1):
                authname = self.papers[i].bibinfo['authors'][k].encode('utf-8')
                out_file.write(', '+authname)
                out_file_tex.write(', '+authname)

            authname = self.papers[i].bibinfo['authors'][max_authors-1].\
                       encode('utf-8')
            if (n_authors == max_authors):
                out_file.write(', &amp; '+authname)
                out_file_tex.write(', \& '+authname)
            else:
                out_file.write(', '+authname)
                out_file_tex.write(', '+authname)

            if (n_authors > 5):
                out_file.write(', &amp; ' + str(n_authors-max_authors) +
                               ' coauthors')
                out_file_tex.write(', \& ' + str(n_authors-max_authors) +
                                   ' coauthors')

            out_file_ascii.write(self.papers[i].bibinfo['authors'][0].encode('utf-8'))
            for k in range(1,n_authors-1):
                out_file_ascii.write(', '+self.papers[i].bibinfo['authors'][k].encode('utf-8'))
            out_file_ascii.write(', & '+self.papers[i].bibinfo['authors'][n_authors-1].encode('utf-8'))

            comma_loc = self.papers[i].bibinfo['journal'].find(',')
            shortjournal = self.papers[i].bibinfo['journal'][0:comma_loc]

            if (shortjournal == 'The Astrophysical Journal' or
                shortjournal == 'Astrophysical Journal v.463' or
                shortjournal == 'Astrophysical Journal'):
                longjournal = 'The Astrophysical Journal'
                shortjournal = 'ApJ'
            if (shortjournal == 'The Astrophysical Journal Letters' or
                shortjournal == 'Astrophysical Journal Letters v.446'):
                longjournal = 'The Astrophysical Journal Letters'
                shortjournal = 'ApJL'
            elif (shortjournal == 'The Astrophysical Journal Supplement Series' or
                  shortjournal == 'The Astrophysical Journal Supplement'):
                longjournal = 'The Astrophysical Journal Supplement Series'
                shortjournal = 'ApJS'
            elif shortjournal == 'The Astronomical Journal':
                longjournal = 'The Astronomical Journal'
                shortjournal = 'AJ'
            elif (shortjournal == 'Publications of the Astronomical Society of the Pacific'
                  or shortjournal == 'The Publications of the Astronomical Society of'+
                  ' the Pacific'):
                longjournal = 'Publications of the Astronomical Society of the Pacific'
                shortjournal = 'PASP'
            elif shortjournal == 'Monthly Notices of the Royal Astronomical Society':
                longjournal = 'Monthly Notices of the Royal Astronomical Society'
                shortjournal = 'MNRAS'
            elif (shortjournal == 'Astronomy and Astrophysics' or
                  shortjournal == 'Astronomy & Astrophysics'):
                longjournal = 'Astronomy & Astrophysics'
                shortjournal = 'A&amp;A'
            elif shortjournal == 'Publications of the Astronomical Society of Japan':
                longjournal = 'Publications of the Astronomical Society of Japan'
                shortjournal = 'PASJ'
#            elif shortjournal == '':
#                shortjournal = ''

            shortjournal_tex = shortjournal
            if shortjournal == 'A&amp;A':
                shortjournal_tex = 'A\&A'

            out_file.write(' ' + self.papers[i].bibinfo['date'].encode('utf-8') + ', ' +
                           shortjournal.encode('utf-8') + ', ' +
                           self.papers[i].bibinfo['volume'].encode('utf-8') + ', ' +
                           self.papers[i].bibinfo['page'].encode('utf-8'))

            out_file_tex.write(' ' + self.papers[i].bibinfo['date'].encode('utf-8') + ', ' +
                               shortjournal_tex.encode('utf-8') + ', ' +
                               self.papers[i].bibinfo['volume'].encode('utf-8') + ', ' +
                               self.papers[i].bibinfo['page'].encode('utf-8') + '\n\n')
            
            out_file_ascii.write('\n ' + longjournal.encode('utf-8') + ', ' +
                                 self.papers[i].bibinfo['volume'].encode('utf-8') + ', ' +
                                 self.papers[i].bibinfo['page'].encode('utf-8') + ', ' +
                                 self.papers[i].bibinfo['date'].encode('utf-8') + '\n\n')

            out_file.write('</p>')
            out_file.write('\n')
            
        out_file.write('<hr />\n')
        out_file.write('<p>\n')
        out_file.write('Created with <a href="pyadspapers.py">PyADSPapers</a>. '+
                       '(use at your own risk)<br />\n')
        out_file.write('Copyright &copy; 2012\n')
        out_file.write('<a href="http://www.stsci.edu/~kgordon/kgordon.html">' +
                       'Karl D. Gordon</a>\n')
        out_file.write('All Rights Reserved\n')
        out_file.write('</p>\n')
        
        out_file.write('</body>\n')
        out_file.write('</html>\n')
    
# creating the pages for me
if __name__ == "__main__":
    
    # these should probably go to command line parameters
    # or at least allow overrides
    use_cache = 0
    lastname = "Gordon"
    firstinitial = "K"

    if use_cache:
        refpapers = pickle.load(open("cache/"+lastname+"_"+firstinitial+".p",
                                     "rb" ))
    else:
        refpapers = Papers(lastname,firstinitial,"1990")
        pickle.dump(refpapers, open("cache/"+lastname+"_"+firstinitial+".p",
                                    "wb" )) # pickle the object

    nonref_bibcodes = ['1997PASP..109.1190G',
                       '1997PhDT.........7G',
                       '2011BSRSL..80..346B',
                       '2005JRASC..99R.135C',
                       '2016MNRAS.455..244R']

    listpapers = lotsofpapers()

#    for i in range(50):
    for i in range(len(refpapers.bibcodes)):
        if ((refpapers.bibcodes[i][0] in ['1','2']) and 
                 not (refpapers.bibcodes[i] in nonref_bibcodes)):
            print("working on " + refpapers.bibcodes[i])

            if use_cache:
                refpaper = pickle.load(open("cache/"+refpapers.bibcodes[i]+".p",
                                            "rb" ))
            else:
                refpaper = Paper(refpapers.bibcodes[i],1)
                pickle.dump(refpaper, open("cache/"+refpaper.bibcode+".p",
                                           "wb" )) # pickle the object
                
            #donot_display = [string.find(refpaper.bibinfo['title'],'Erratum'),
            #                 string.find(refpaper.bibinfo['title'],
            #                             'Corrigendum')]
            donot_display = [refpaper.bibinfo['title'].find('Erratum'),
                             refpaper.bibinfo['title'].find('Corrigendum')]
            if (sum(donot_display) == -1*len(donot_display)):

                refpaper.WriteHtml()
                listpapers.papers.append(refpaper)
            else:
                print("not working on " + refpapers.bibcodes[i])

        else:
            print("not working on " + refpapers.bibcodes[i])

    listpapers.WriteHtml('Gordon','Karl','date')

    listpapers.WriteHtml('Gordon','Karl','cites')

    listpapers.WriteHtml('Gordon','Karl','cites_per_year')

    listpapers.WriteHtml('Gordon','Karl','n_authors')

    listpapers.WriteHtml('Gordon','Karl','author_rank')

    # make the word cloud for paper titles
#    title_text = ''
#    for i in range(len(listpapers.papers)):
#        title_text += listpapers.papers[i].bibinfo['title'].encode('utf-8')
#    
#    tags = make_tags(get_tag_counts(title_text), maxsize=120)
#    
#    create_tag_image(tags, lastname+'_'+firstinitial+'.png', size=(900, 600))
