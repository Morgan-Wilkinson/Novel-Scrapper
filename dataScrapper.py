from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout,
    QHBoxLayout,
    QApplication,
    QCheckBox,
    QComboBox,
    QPushButton,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QSlider,
    QSpinBox,
)
import sys
import os
import re
from reportlab.pdfgen import canvas 
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors 
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from pypdf import PdfMerger
import time
from novels import novels

class MainWindow(QMainWindow):
  freewebnovel_base_url = 'https://freewebnovel.com'
  current_novel_name = ''
  current_novel_url = ''
  beginning = True
  starting_chapter = 0
  save_path = os.getcwd()

  def __init__(self):
      super().__init__()

      self.setWindowTitle("Project Scrapper")

      # Novel List Label 
      self.novel_list_label = QLabel("Novels Available")
      self.novel_list_label.setAlignment(Qt.AlignLeft)
      # Novel Combo Box
      self.novel_list = QComboBox()
      self.novel_list.addItems(self.getAvailableNovels().keys())
      self.novel_list.currentTextChanged.connect( self.novel_changed )

      # Novel Chapter Selector
      self.novel_chapter_selector = QSpinBox()
      self.novel_chapter_selector.setDisabled(True)
      self.novel_chapter_selector.setMaximum(9999)
      self.novel_chapter_selector.setRange(0,9999)
      self.novel_chapter_selector.setSingleStep(1)
      self.novel_chapter_selector.valueChanged.connect(self.novel_chapter_changed)

      # File Dialog Label & Button
      self.file_dialog_label = QLabel(self.save_path)
      self.file_dialog_button = QPushButton("Select Folder")
      self.file_dialog_button.setCheckable(False)
      self.file_dialog_button.clicked.connect(self.open_file_diaglog)

      # Begin Download Button
      self.download_button = QPushButton("Begin")
      self.download_button.setCheckable(False)
      self.download_button.setDisabled(True)
      self.download_button.clicked.connect(self.begin_download)
      
      
      # Add widgets to central layout
      self.vertical_layout = QVBoxLayout()
      self.vertical_layout.addWidget(self.novel_list_label)

      # Novel and Chapter Layout
      self.novel_chapter_layout = QHBoxLayout()
      self.novel_chapter_layout.addWidget(self.novel_list)
      self.novel_chapter_layout.addWidget(self.novel_chapter_selector)
      
      # File Dialog Layout
      self.file_dialog_layout = QHBoxLayout()
      self.file_dialog_layout.addWidget(self.file_dialog_label)
      self.file_dialog_layout.addWidget(self.file_dialog_button)

      # Container Vertical Layout
      self.vertical_layout.addLayout(self.novel_chapter_layout)
      self.vertical_layout.addLayout(self.file_dialog_layout)
      self.vertical_layout.addWidget(self.download_button)
      
      # Progress Label
      self.progress_label = QLabel()
      self.vertical_layout.addWidget(self.progress_label)

      # Create overall widget and add the layout to it  
      self.container = QWidget()
      self.container.setLayout(self.vertical_layout)

      self.setCentralWidget(self.container)
  
  # Tracks if the novel selected in the GUI has changed
  def novel_changed(self, i):
    self.current_novel_name = i
    self.current_novel_url = novels.get(i)
    self.progress_label.setText("")
    if i != "":
      self.novel_chapter_selector.setDisabled(False)
      self.download_button.setDisabled(False)
    else:
      self.novel_chapter_selector.setDisabled(True)
      self.download_button.setDisabled(True)

  # Tracks the current chapter number selected to start downloading from.
  def novel_chapter_changed(self, i):
    if i != 0: 
      self.beginning = False
      self.starting_chapter = i
      res = re.sub(r'\d', str(i), self.get_current_novel_base())
      self.current_novel_url = res
    else:
      self.beginning = True
      self.starting_chapter = 0
      self.current_novel_url = self.get_current_novel_base()

  # File Dialog opener method.
  def open_file_diaglog(self):
    self.folder_path = QFileDialog.getExistingDirectory(self, 'Select Folder')
    self.file_dialog_label.setText(self.folder_path)
    self.save_path = self.folder_path

  # Retrieves the novel's base url from the JSON of available novels
  def get_current_novel_base(self):
    return novels.get(self.current_novel_name)

  # Retrieves the available novel for download.
  def getAvailableNovels(self):
    return novels
  
  # Download method. It handles the validation and requests retrieval and creation of PDFs. 
  def begin_download(self):
    #  Validation step
     self.progress_label.setText("")
     if self.current_novel_name == '':
        self.progress_label.setText("Please select a novel to download")
        return
     else:
        self.progress_label.setText("Started download for {0}".format(self.current_novel_name))
        styles = getSampleStyleSheet()
        styleN = styles['Normal']

        while self.current_novel_url != '':
          # Send an HTTP GET request to the website
          response = requests.get(self.current_novel_url)

          # Parse the HTML code using BeautifulSoup
          soup = BeautifulSoup(response.content, 'html.parser')

          # Extract the relevant information from the HTML code
          # Title
          current_chapter_title = soup.find("span", {"class": "chapter"}).get_text()
          current_chapter_title = current_chapter_title.replace(":", "" )
          current_chapter_title = current_chapter_title.replace("(", "" )
          current_chapter_title = current_chapter_title.replace(")", "" )
          current_chapter_title = current_chapter_title.replace("/", "" )

          # Chapter Text
          current_chapter = soup.find(id="article")
          current_chapter_array = []
          for paragraph in current_chapter.find_all('p'):
            current_chapter_array.append(paragraph.get_text())
            current_chapter_array.append('<br/><br/>')
          

          # Create PDF
          story = []
          pdf_name = "{0}.pdf".format(current_chapter_title)
          doc = SimpleDocTemplate(
              self.create_file_path(pdf_name),
              pagesize=letter,
              bottomMargin=.4 * inch,
              topMargin=.6 * inch,
              rightMargin=.8 * inch,
              leftMargin=.8 * inch)

          for para in current_chapter_array:
            P = Paragraph(para, styleN)
            story.append(P)

          doc.build(story,)

          # Next Chapter
          next_chapter = soup.find(id='next_url')
          if 'chapter' not in next_chapter['href']:
            self.current_novel_url = ''
          else:
             self.current_novel_url = self.freewebnovel_base_url + next_chapter['href']

          # Add a delay between requests to avoid overwhelming the website with requests
          time.sleep(5)
        
        self.merge_pdfs()
        self.progress_label.setText("Download Complete")

  # Method to merge all the singular chapters into one single PDF book.
  def merge_pdfs(self):
    pdf_merger = PdfMerger()
    folder_path = Path(self.create_folder_path()).glob("*.pdf")
    folder_path_list = []
    for path in folder_path:
     folder_path_list.append(str(path))

    folder_path_list.sort(key=self.natural_keys)
    for path in folder_path_list:
      pdf_merger.append(path)
    pdf_merger.write("{0}/{1}/{2}.pdf".format(self.save_path, self.current_novel_name, self.current_novel_name))

  # Method to create the folders in which the PDF's would be saved.
  def create_folder_path(self):
    outfiledir = '{0}/{1}/Chapters/'.format(self.save_path, self.current_novel_name)
    if not os.path.exists('{0}/{1}'.format(self.save_path, self.current_novel_name)):
      os.mkdir('{0}/{1}'.format(self.save_path, self.current_novel_name))
      if not os.path.exists('{0}/{1}/Chapters'.format(self.save_path, self.current_novel_name)):
        os.mkdir('{0}/{1}/Chapters'.format(self.save_path, self.current_novel_name))
    outfolderpath = os.path.join(outfiledir)
    return outfolderpath
  
  # Method to create the PDF file path.
  def create_file_path(self, file_name):
    outfilename = file_name
    outfiledir = '{0}/{1}/Chapters/'.format(self.save_path, self.current_novel_name)
    if not os.path.exists('{0}/{1}'.format(self.save_path, self.current_novel_name)):
      os.mkdir('{0}/{1}'.format(self.save_path, self.current_novel_name))
      if not os.path.exists('{0}/{1}/Chapters'.format(self.save_path, self.current_novel_name)):
        os.mkdir('{0}/{1}/Chapters'.format(self.save_path, self.current_novel_name))
    outfilepath = os.path.join( outfiledir, outfilename )
    return outfilepath

  def atoi(self, text):
    return int(text) if text.isdigit() else text

  # Utility sort method.
  def natural_keys(self, text):
    '''
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    '''
    return [ self.atoi(c) for c in re.split(r'(\d+)', text) ]
    
app = QApplication(sys.argv)
w = MainWindow()
w.show()
app.exec_()