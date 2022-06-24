import re
import shutil
from six.moves import urllib
import socket
import tarfile
import os
import sys
import pypandoc
import pandas as pd
import arxiv
import linecache

LINK_PATH = "C:\python_project\paper_download\contact angle\paper_url_text.txt"
NAME_PATH = "C:\python_project\paper_download\contact angle\paper_name.txt"
TEX_SAVE_PATH = "C:\python_project\paper_download\contact angle\papers_tex"
FILE_PATH='C:\python_project\paper_information_search\\txt_file'
info_all = []
info_one_paper = []
info_dic = {"theta_name":"","theta_num":""}


def get_authors(authors, first_author=False):
    output = str()
    if first_author == False:
        output = ", ".join(str(author) for author in authors)
    else:
        output = authors[0]
    return output


def sort_papers(papers):
    output = dict()
    keys = list(papers.keys())
    keys.sort(reverse=True)
    for key in keys:
        output[key] = papers[key]
    return output


def get_daily_papers(query=" ", max_results=20):
    """
    @param query: str
    @return paper_with_code: dict
    """

    # output
    content = dict()

    search_engine = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )

    for result in search_engine.results():

        paper_id = result.get_short_id()
        paper_title = result.title
        paper_url = result.entry_id
        paper_url_pdf=paper_url.replace('abs','pdf')
        paper_url_link.append(paper_url_pdf)
        paper_title_new=paper_title.replace(':',' ')
        paper_name.append(paper_title_new)

        paper_abstract = result.summary.replace("\n", " ")
        paper_authors = get_authors(result.authors)
        paper_first_author = get_authors(result.authors, first_author=True)
        primary_category = result.primary_category

        publish_time = result.published.date()

        print("Time = ", publish_time,
              " title = ", paper_title,
              " author = ", paper_first_author)

def _get_file_urls(file_url_txt):
    base_url = "http://arxiv.org"
    tex_link = '/e-print/'
    file = open(file_url_txt, 'r')
    file_url=[]
    for line in file.readlines():
        line=line.split("/pdf/")[-1].rstrip()
        file_url.append(base_url+tex_link+line)
    print(file_url)
    file.close()
    return file_url


def download(file_link, save_path):
    socket.setdefaulttimeout(30)
    download_failed_url = []
    for url, index in zip(file_link, range(len(file_link))):
        filename = url.split('/')[-1]+".tar.gz"
        tem_path = save_path
        tem_path = os.path.join(tem_path, filename)
        try:
            urllib.request.urlretrieve(url, tem_path)
        except socket.timeout or urllib.error.ContentTooShortError:
            count = 1
            while count <= 5:
                try:
                    urllib.request.urlretrieve(url, tem_path)
                    break
                except socket.timeout or urllib.error.ContentTooShortError:
                    err_info = 'Reloading for %d time' % count if count == 1 else 'Reloading for %d times' % count
                    print(err_info)
                    count += 1
            if count > 5:
                print("downloading file failed!try again later")
                download_failed_url.append(url+'\n')
                f = open(os.path.join(TEX_SAVE_PATH, "corrupted_file.txt"), 'w')
                f.writelines(download_failed_url)
                continue

        sys.stdout.write('\r>> Downloading %.1f%%' % (float(index + 1) / float(len(file_link)) * 100.0))
        sys.stdout.flush()
    print('\nSuccessfully downloaded')


def extract(file_folder=TEX_SAVE_PATH):
    corrupted_file=[]
    corrupted_file_number = 0
    for tarfile_name,index in zip(os.listdir(file_folder),range(len(os.listdir(file_folder)))):
        tarfile_path = os.path.join(file_folder,tarfile_name)
        try:
            tar = tarfile.open(tarfile_path)
            names = tar.getnames()
            if not os.path.isdir(tarfile_path.strip(".tar.gz")):
                os.mkdir(tarfile_path.strip(".tar.gz"))
            for name in names:
                tar.extract(name, tarfile_path.strip(".tar.gz"))
            tar.close()
        except:
            corrupted_file.append(tarfile_name+'\n')
            f=open(os.path.join(TEX_SAVE_PATH,"corrupted_file.txt"),'w')
            f.writelines(corrupted_file)
            corrupted_file_number += 1
            print("file corruption, please try to download again")
            continue

        sys.stdout.write('\r>> Extracting %.1f%%\n'% (float(index + 1) / float(len(os.listdir(file_folder))) * 100.0))
        sys.stdout.flush()

    print("corrupted %d files"%corrupted_file_number)
    print("Account for %.2f"%(corrupted_file_number/len(os.listdir(file_folder))))


def get_file_list(input_dir,file_pattern):
    target_path = input_dir
    file_names = []
    for dirpath, dirnames, filenames in os.walk(target_path):
        for file_name in filenames:
            if os.path.splitext(file_name)[-1] == file_pattern:
                file_names.append(os.path.join(dirpath, file_name))
    return file_names


def tex_to_txt(input_dir,target_pattern):
    file_name=get_file_list(input_dir,target_pattern)
    print(file_name)
    file_index = []
    for j in range(len(file_name)):
        index = str(file_name[i].split("\\")[-2])+".txt"
        output_file = os.path.join(FILE_PATH,index)
        shutil.copy(src=file_name[i],dst=output_file)
        pypandoc.convert_file(file_name[i], to='docx', outputfile=output_file)
        file_index.append(index)


def store_info_to_csv(result_str):
    pattern_number = "\d+\.?\d*"
    pattern_name = "{\w+"
    result_theta = re.compile(pattern_number).findall(result_str)
    result_name = re.compile(pattern_name).findall(result_str)
    result_name[0] = result_name[0].replace("{","")
    print(result_theta[0])
    df =pd.DataFrame()
    global info_dic,info_one_paper
    info_dic = { "theta_name": "θ"+result_name[0], "theta_num": result_theta[0]}
    print(info_dic)
    info_one_paper.append(info_dic)
    info_dic = {"theta_name":"","theta_num":""}


def search_str_in_tex(base_path,file_pattern,target_str):
    file_path = get_file_list(base_path,file_pattern)
    for file in file_path:
        count = 1
        print(file.split("\\")[-1])
        print("Extracting number %d file's info"% count)
        info_one_paper.append(str(file.split("\\")[-1]))
        lines = open(file, "r", encoding="UTF-8", errors="ignore").readlines()
        for line in lines:
            search_info = re.compile(target_str)
            n = search_info.search(line)
            m = re.findall(target_str,line)
            if n:
                print(n.group())
                store_info_to_csv(n.group())
        count +=1

if __name__ == "__main__":
    paper_url_link=[]
    paper_name=[]
    # data_collector = []
    # keywords = dict()
    # keywords["contact angle"] = "\"contact angle\""
    #
    # for topic, keyword in keywords.items():
    #     print("Keyword: " + topic)
    #     get_daily_papers(query=keyword, max_results=1000)
    #     print("\n")
    #
    # paper_url_file=open('contact angle/paper_url_link.txt', 'w')
    # for i in range(len(paper_url_link)):
    #     paper_url_file.write(paper_url_link[i]+'\n')
    #
    # paper_url_file=open('contact angle/paper_name.txt', 'w')
    # for i in range(len(paper_name)):
    #     paper_url_file.write(paper_name[i]+'\n')

    # File_url_txt = LINK_PATH
    # File_link = _get_file_urls(File_url_txt)
    # download(File_link, TEX_SAVE_PATH)
    # extract()

    search_str = ["theta_+{\w+}=+\d+(\.\d+)?"]

    for i in range(len(search_str)):
        search_str_in_tex(os.path.join(FILE_PATH),file_pattern='.txt',target_str=search_str[i])