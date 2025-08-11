docker build -t tg_bot_image .

docker run -it -d --restart=unless-stopped --name tg_bot_container tg_bot_image

docker save -o tg_bot.tar tg_bot_image

docker load -i tg_bot.tar
