import matplotlib.pyplot as plt
from PIL import Image
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator


def visualizar_palabras(dialogs):
    lista = ''
    for dialog in dialogs:
        lista = lista + dialog[1]
    wordcloud = WordCloud(
        background_color='white',
        max_font_size=50,
        random_state=42
    ).generate(str(lista))
    print(wordcloud)
    fig = plt.figure(1)
    plt.imshow(wordcloud)
    plt.axis('off')
    plt.show()


def main():
    pass


if __name__ == '__main__':
    main()
    print('FIN PROCESO')
