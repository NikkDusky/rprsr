# reactor parser by Nikk Dusky [3.0.2]
# UPD new in 3.0.0 - 3.0.2
# Checking content hashes
# Script rewrited [OOP]


from os import system, remove, listdir, path, mkdir
from time import sleep, strftime
from shutil import rmtree
from sys import stdout
import hashlib
import ast
import re


try:
    from loguru import logger
except ModuleNotFoundError:
    print("Loguru не найден. Устанавливаю Loguru.")
    system("pip install loguru")
    from loguru import logger

try:
    import requests
except ModuleNotFoundError:
    logger.error("Requests не найден!")
    logger.info("Попытка установить requests.")
    system("pip install requests")
    import requests
    logger.success("Requests установлен!")

try:
    from bs4 import BeautifulSoup
except ModuleNotFoundError:
    logger.error("bs4 не найден!")
    logger.info("Попытка установить bs4.")
    system("pip install beautifulsoup4")
    from bs4 import BeautifulSoup
    logger.success("bs4 установлен!")

try:
    from PIL import Image, ImageSequence
except ModuleNotFoundError:
    logger.error("Pillow не найден!")
    logger.info("Попытка установить Pillow.")
    system("pip install Pillow")
    from PIL import Image, ImageSequence
    logger.success("Pillow установлен!")

try:
    import configparser
except ModuleNotFoundError:
    logger.error("configparser не найден!")
    logger.info("Попытка установить configparser.")
    system("pip install configparser")
    import configparser
    logger.success("configparser установлен!")

try:
    import telebot
except ModuleNotFoundError:
    logger.error("PyTelegramBotAPI не найден!")
    logger.info("Попытка установить PyTelegramBotAPI.")
    system("pip install pyTelegramBotAPI")
    import telebot
    logger.success("PyTelegramBotAPI установлен!")


#Main class
@logger.catch()
class Parser():
    def __init__(self):
        #Handlers for loguru
        config = {
            "handlers": [
                {"sink": stdout, "format": "[<light-cyan>{time:YYYY-MM-DD HH:mm:ss}</light-cyan>] [<level>{level}</level>] <level>{message}</level>"},
                {"sink": "debug.log", "diagnose": False, "compression": "zip", "encoding": "utf8", "rotation": "10 MB", "format": "[<cyan>{time:YYYY-MM-DD HH:mm:ss}</cyan>] [<level>{level}</level>] {message}"},
                        ]
                }

        logger.configure(**config) #Configure loguru with handlers
        new_level = logger.level("FORMAT", no=38, color="<le>") #new level for logging file formats [.png; .jpg; .jpeg; .gif;]
        new_content = logger.level("NEW", no=38, color="<lg>") #new level for checked content
        old_content = logger.level("OLD", no=38, color="<r>") #new level for checked content

        self.d_dict = {} #variable for tags dict
        self.pic_number = 1 #variable for content counting

        logger.info("Все библиотеки присутствуют, начинаю работу.")
        logger.info("*=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=*")
        logger.info("             reactor parser              ")
        logger.info(f"               [{strftime('%X')}]       ")
        logger.info("*=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=*")

        self.cfg_file = "settings.ini" #set config name
        self.config = configparser.ConfigParser() #init configparser

        self.checkConfigExistAndTakeVariables() #start func (Check Files, Take variables from settings.ini)
        self.checkTempFolderExist() #start func (Check temp folder for content)
        self.checkHashesFileExist() #start func (Check hashes file)
        self.setupBot() #start func (setup telegram bot)
        self.createTagsTempFile() #start func (create tags.txt temp file)
        self.setupHeaders() #start func (setup headers for parsing)

        self.mainWorker() #start func (run parser / WORK! WORK! WORK!)

    def exitFromApp(self): #simple func for waiting press key and exit from app
        input("Нажмите Enter, чтобы закрыть приложение...")
        exit()

    #create config func (set sections & parameters / write settings.ini)
    def createConfig(self, total_number=-1, token="YOUR_TOKEN_HERE", sleep="4", send_channel=f"@your_channel_here", link="http://anime.reactor.cc/best", end_page=f"-1", folder=f"anime_best", tags="tags.txt"):
        self.config.add_section("bot_settings")
        self.config.set("bot_settings", "bot_token", f"{token}")
        self.config.set("bot_settings", "bot_sleep", f"{sleep}")
        self.config.set("bot_settings", "send_channel", f"{send_channel}")

        self.config.add_section("link_settings")
        self.config.set("link_settings", "link", f"{link}")
        self.config.set("link_settings", "total_pages", f"{total_number}")
        self.config.set("link_settings", "end_page", f"{end_page}")

        self.config.add_section("temp_files")
        self.config.set("temp_files", "folder", f"{folder}")
        self.config.set("temp_files", "tags", f"{tags}")

        with open(self.cfg_file, "w") as config_file:
            self.config.write(config_file)
        logger.success(f"Файл '{self.cfg_file}' сформирован.")

    #upd config function (just for total_pages saving)
    def updateConfig(self, total_number=-1, token="YOUR_TOKEN_HERE", sleep="4", send_channel=f"@your_channel_here", link="http://anime.reactor.cc/best", end_page=f"-1", folder=f"anime_best", tags="tags.txt"):
        logger.info(f"Обновляю {self.cfg_file}: Общее количество страниц {self.total_pages}.")
        self.config.set("bot_settings", "bot_token", f"{token}")
        self.config.set("bot_settings", "bot_sleep", f"{sleep}")
        self.config.set("bot_settings", "send_channel", f"{send_channel}")

        self.config.set("link_settings", "link", f"{link}")
        self.config.set("link_settings", "total_pages", f"{total_number}")
        self.config.set("link_settings", "end_page", f"{end_page}")

        self.config.set("temp_files", "folder", f"{folder}")
        self.config.set("temp_files", "tags", f"{tags}")

        with open(self.cfg_file, "w") as config_file:
            self.config.write(config_file)

    #check exists config
    def checkConfigExistAndTakeVariables(self):
        if path.isfile(self.cfg_file): #Check config exists
            logger.info(f"Конфиг файл '{self.cfg_file}' обнаружен.")
        else:
            logger.error(f"Конфиг файл '{self.cfg_file}' не найден. Создаю новый.")
            self.createConfig() #Create config
            logger.error("Задайте: Токен, Канал, Ссылку, Папку.")
            logger.error("Задайте: Общее количество страниц.")
            self.exitFromApp()

        self.config.read(self.cfg_file) #Read the config file

        #else config exists, take variables
        try:
            self.bot_token = self.config.get("bot_settings", "bot_token")
            self.bot_time_sleep = int(self.config.get("bot_settings", "bot_sleep"))

            self.channel_name = self.config.get("bot_settings", "send_channel")

            self.Link = self.config.get("link_settings", "link")
            self.folder = self.config.get("temp_files", "folder")
            self.filename = self.config.get("temp_files", "tags")
            self.total_pages = int(self.config.get("link_settings", "total_pages"))
            self.end_page = int(self.config.get("link_settings", "end_page"))
        except:
            #Exception (settings.ini corrupted? Del, Exit. Run app. Make new config.)
            logger.error("Некоторые настройки в конфиг файле не найдены.")
            self.delConfig(self.cfg_file) #Delete config
            self.exitFromApp()

    #del config func
    def delConfig(self, config_name: str) -> None:
        logger.success("Удаляю старый конфиг файл.")
        remove(config_name)
        logger.error("ВНИМАНИЕ! Перезапустите скрипт!")

    #check temp folder exist
    def checkTempFolderExist(self):
        #Check temp folder exists
        if path.isdir(f"{self.folder}"): #If temp folder exist, del, make new clear space.
            logger.info(f"Папка '{self.folder}' обнаружена. Очищаю и создаю новую.")
            rmtree(f"{self.folder}")
            mkdir(f"{self.folder}")
        else: #Else not found, make new folder.
            logger.info(f"Папка '{self.folder}' не найдена. Создаю новую.")
            mkdir(f"{self.folder}")

    #Check hashes file exist
    def checkHashesFileExist(self):
        if path.isfile("hashes"):
            logger.info("Файл hashes обнаружен.")
        else:
            logger.error("Файл hashes не найден.")
            self.createHashesFile()
            logger.success("Файл hashes создан.")

    #Setup bot func
    def setupBot(self):
        self.bot = telebot.TeleBot(self.bot_token)

    #Create tags temp file func
    def createTagsTempFile(self):
        f = open(self.filename, 'w', encoding='utf8')
        f.close()

    #Create hashes file
    def createHashesFile(self):
        hashesFile = open('hashes', 'w', encoding='utf8')
        hashesFile.close()

    #Setup headers for parser
    def setupHeaders(self):
        self.HEADERS = {
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
                }

    #Get pictures in folder
    def get_files(self, folder_name: str) -> None:
        return listdir(folder_name)

    #Check content hash
    def check_hash(self, folder: str, img: str) -> bool:
        openedFile = open(f'{folder}\\{img}', 'rb') #Open file
        md5Hash = hashlib.md5(openedFile.read()).hexdigest() #Calculate hash
        with open("hashes", "r", encoding='utf8') as hashFile: #Open hashes, get lines
            hashList = []
            for line in hashFile:
                hashList.append(line.rstrip("\n"))

        #If hash in hashes return False, else add hash in hashes & return True
        if md5Hash in hashList:
            logger.log("OLD", f"Картинка {img} является не новой.")
            return False
        else:
            logger.log("NEW", f"Картинка {img} является новой. Записываю hash в hashes.")
            with open("hashes", "a", encoding='utf8') as hashFile:
                hashFile.write(f"{md5Hash}\n")
            return True

    #Picture dealing func
    def send_to_channel(self):
        files_to_send = self.get_files(self.folder)
        files_to_send.sort(key=lambda f: int(re.sub('\D', '', f))) #sorting list from 1 - n fixing first send like 1, 10, 11
        with open(self.filename, "r") as f:
            self.d_dict = f.read()
        self.d_dict = ast.literal_eval(self.d_dict) #Convert tags string to dictionary with ast lib

        for img in files_to_send: #Get tag number with pic number
            tag_number = int(img.replace(".jpg", "").replace(".gif", ""))

            #call check_hash (returns True/False)
            if self.check_hash(self.folder, img):
                logger.info(f'Отправляю изображение: {self.folder}\\{img}')
                photo = open(f'{self.folder}\\{img}', 'rb')
                
                if img.endswith(".jpg"): #If .jpg -> bot.send_photo
                    self.bot.send_photo(self.channel_name, photo, f"{self.d_dict[tag_number]}") #Send picture
                    photo.close()
                    logger.info(f"Удаляю файл: {self.folder}\\{img}")
                else: #Else this is gif -> bot.send_video
                    self.bot.send_video(self.channel_name, photo, None, f"{self.d_dict[tag_number]}")
                    photo.close()
                    logger.info(f"Удаляю файл: {self.folder}\\{img}")

                sleep(self.bot_time_sleep) #Sleep send function
                
            else:
                pass
            remove(f"{self.folder}\\{img}") #Remove sended picture
            

    #Get html for parsing
    def get_html(self, url, params=None):
        r = requests.get(url, headers=self.HEADERS, params=params)
        return r

    #hashtags regex converter
    def convert_string(self, string: str) -> str:
        string = re.sub('[^a-zA-Z$,]', "", string).replace(",", " #").replace("# ", "")
        string = string.rstrip("#")
        string = re.sub('[^#a-zA-Z$, ]', "", string)
        string = "#" + string.lower()
        string = re.sub('# ', "", string)
        return string

    #Pictures convert and save
    def resize_and_save(self, link: str, tags: list, number_of_pic: int) -> None:
        pic_list = ['.jpg', '.jpeg', '.png']
        converted_tags = self.convert_string(tags)
        if converted_tags.startswith("#"):
            self.d_dict[number_of_pic]=f"{converted_tags}"
        else:
            self.d_dict[number_of_pic]="#none"

        if link.endswith(('.jpg', '.jpeg', '.png')):
            logger.log("FORMAT", f"Ссылка ведёт на .jpg/.jpeg./.png - сохраняю как {number_of_pic}.jpg")
            r = requests.get(link, stream=True)
            r.raw.decode_content = True

            im = Image.open(r.raw)
            width, height = im.size
            im = im.convert('RGB')
            im_crop = im.crop((0, 0, width, height-15)) #Crop img bottom banner from site
            im_crop.save(f'{self.folder}\\{number_of_pic}.jpg', quality=100)
        else:
            logger.log("FORMAT", f"Ссылка ведёт на .gif - сохраняю как {number_of_pic}.gif")
            response = requests.get(link, stream=True)
            response.raw.decode_content = True

            im = Image.open(response.raw)
            width, height = im.size
            frames = ImageSequence.Iterator(im)
            def thumbnails(frames): #Crop bottom banner from .gif frames.
                for frame in frames:
                    thumbnail = frame.copy()
                    thumbnail.thumbnail(im.size, Image.ANTIALIAS)
                    thumbnail = thumbnail.crop((0, 0, width, height-15))
                    yield thumbnail
            frames = thumbnails(frames)
            om = next(frames)
            om.info = im.info
            om.save(f'{self.folder}\\{number_of_pic}.gif', save_all=True, append_images=list(frames), loop=0)

    #Content parser
    def get_content(self, html: str) -> None:
        links = []
        tags = []
        self.d_dict = {}

        soup = BeautifulSoup(html, 'html.parser')
        posts = soup.find_all('img')

        logger.info(f"Собираю массив картинок со страницы: {self.total_pages}.")
        for post in posts:
            link = str(post["src"])
            if  link.startswith("http://img2.reactor.cc/pics/post/") or link.startswith("http://img10.reactor.cc/pics/post/") or link.startswith("http://img2.joyreactor.cc/pics/post"):
                links.append(post["src"])
                try:
                    tags.append(post["alt"])
                except:
                    tags.append("None")

        logger.info(f"Сохраняю/обрезаю. В очереди: {len(links)} картинок ({self.pic_number} - {self.pic_number + int(len(links)) - 1})")
        for counter in range(len(links)):
            self.resize_and_save(links[counter], tags[counter], self.pic_number)
            self.pic_number += 1
        with open(self.filename, "w") as f:
            f.write(f"{self.d_dict}")

    #Get response from url
    def parse(self, ParseLink: str) -> None:
        self.html = self.get_html(ParseLink)
        if self.html.status_code == 200:
            self.get_content(self.html.text)
        else:
            logger.error("Error status code != 200")
            exit()

    #Main work func with while True
    def mainWorker(self):
        if self.bot_token == "YOUR_TOKEN_HERE" or self.bot_time_sleep < 4 or self.channel_name == "@your_channel_here" or self.Link == "" or self.folder == "" or self.filename == "" or self.total_pages <= -1 or self.end_page < -1:
            raise NameError("""
        Файл 'settings.ini' составлен некорректно:

        - Возможно вы не указали bot_token;
        - Возможно bot_sleep < 4;
        - Возможно вы не указали send_channel;
        - Возможно link пустой;
        - Возможно total_pages <= -1;
            + Для того чтобы указать верное общее количество страниц и максимально
            избежать дублирований картинок при отправке в канал перейдите по своей link
            (ссылке с тематикой/тэгом), а затем перейдите на следующую страницу,
            в адресной строке браузера в конце будут цифры.
            + total_pages = цифры + 1;
        - Возможно end_page < -1;
        - Возможно folder пустой;
        - Возможно tags пустой;
        """)
        else:
            logger.info("Файл 'settings.ini' составлен корректно.")
            while True:
                if (self.total_pages != self.end_page):
                    URL = f"{self.Link}/{self.total_pages}"
                    self.parse(URL)
                    self.total_pages -= 1
                    self.updateConfig(self.total_pages, self.bot_token, self.bot_time_sleep, self.channel_name, self.Link, self.end_page, self.folder, self.filename)
                    self.send_to_channel()
                else:
                    logger.info("Готово...")
                    self.exitFromApp()

#Start class
if __name__ == "__main__":
    try:
        Parser()
    except KeyboardInterrupt:
        logger.info("Досрочное завершение работы (CTRL+C).")