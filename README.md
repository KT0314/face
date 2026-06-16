#需安裝以下套件 
pip install opencv-python cvzone==1.5.6 mediapipe==0.10.11 
pip install pandas 
pip install numpy 
pip install requests 
pip install matplotlib 
pip install pygame 
#疲勞駕駛監視器 
#一開始使用者需要注視前方5秒聽到提示升即可，之後如果使用者閉眼超過3秒或打哈欠系統都會發出聲音
#由於我是用Telegram作為傳送訊息的地方，所以如果再Demo沒收到訊息是正常的，不過你也可以自己去創建TelegramBot 
#步驟1.到TelegramApp搜尋@BotFather 對他發送/newbot 接著輸入Bot名稱(以bot為結尾),就可以獲取API  
#步驟2.在 Telegram 搜尋 @userinfobot 然後按我要加入頻道，再按我已加入頻道，就可以獲取ID  
#步驟3.在utils.py把API和ID放上去
