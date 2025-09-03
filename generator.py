import frontmatter as fm
import jinja2 as j2
import json
import markdown2 as md2
import os
import re

image_formats = ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.svg', '.tiff']
desc_path: str = 'cyberpunk 2025'
intro_page: str = f'{desc_path}{os.path.sep}intro.md'
index_file: str = 'index.html'
default_options = json.load(open('default_config.json', 'r', encoding='utf-8'))
combined_diacritics: dict[str, str] = {
    'Ą': 'Ą', 'Ć': 'Ć', 'Ę': 'Ę', 'Ł': 'Ł', 'Ń': 'Ń', 'Ó': 'Ó', 'Ś': 'Ś', 'Ź': 'Ź', 'Ż': 'Ż',
    'ą': 'ą', 'ć': 'ć', 'ę': 'ę', 'ł': 'ł', 'ń': 'ń', 'ó': 'ó', 'ś': 'ś', 'ź': 'ź', 'ż': 'ż'
}


def get_page_sort_key(filename: str) -> str:
    return f'{'#'.join(get_page_group(filename, False))}00#{get_page_title(filename, False)}'


def get_page_group(filename: str, trim_index: bool = True) -> list[str] | None:
    return list(map(lambda name: name[3 if trim_index else 0:], filename.split(os.sep)[1:-1]))


def get_page_title(filename: str, trim_index: bool = True) -> str:
    name: str = re.sub(r'\..+$', '', os.path.basename(filename))[3 if trim_index else 0:]
    title: str = name[0].upper() + name[1:]
    for combining, single in combined_diacritics.items():
        title = title.replace(combining, single)
    return title


def group_diff(old: list[str], new: list[str]) -> list[list[str]]:
    common: list[str] = []
    min_len = min(len(old), len(new))
    di: int
    for i in range(min_len):
        if old[i] == new[i]:
            common.append(old[i])
        else:
            di = i
            break
    else:
        di = min_len
    diff: list[list[str]] = []
    for i in range(di, len(new)):
        diff.append(common + new[di:i + 1])
    return diff


def md2html(markdown: str) -> md2.UnicodeWithAttrs:
    return md2.markdown(markdown, extras=['tables', 'metadata'])


def parse_options(page: str) -> dict[str, object]:
    options: dict[str, object] = fm.load(page).metadata
    return {'initial': options.get('inicjał', default_options['inicjał']),
            'dynamic_image': options.get('dynamiczny ob.', default_options['dynamiczny ob.']),
            'image_scale': options.get('skala ob.', default_options['skala ob.']),
            'image_scale_side': options.get('skala ob. z boku', default_options['skala ob. z boku']),
            'image_scale_wide_screen': options.get('skala ob. szer.', default_options['skala ob. szer.'])}


md_pages: list[str]
html_pages: list[str]


def clean() -> None:
    for file in [*(os.path.relpath(os.path.join(root, file))
                   for root, _, files in os.walk(desc_path)
                   for file in files if file.endswith('.html')), index_file]:
        if os.path.exists(file):
            os.remove(file)


def insert_properties(options: dict[str, object]) -> None:
    for file in [intro_page, *md_pages]:
        page: fm.Post = fm.load(file)
        existing_options: dict[str, object] = page.metadata.copy()
        page.metadata = options.copy()
        page.metadata.update(existing_options)
        for key in page.metadata.copy().keys():
            if key not in options.keys():
                page.metadata.pop(key)
        fm.dump(page, file)


def generate_subsistes(template: j2.Template) -> None:
    for file in md_pages:
        with open(file, 'r', encoding='utf-8') as f:
            image: str | None = None
            for fmt in image_formats:
                image_file: str = file.replace('.md', fmt)
                if os.path.exists(image_file):
                    image = image_file
                    break
            with open(file.replace('.md', '.html'), 'w', encoding='utf-8') as out_file:
                out_file.write(template.render(title=get_page_title(file), content=md2html(f.read()), image=image,
                                               **parse_options(file)))


def generate_main(template: j2.Template) -> None:
    with open(index_file, 'w', encoding='utf-8') as out_file:
        content: str = ''
        image: str | None = None
        for fmt in image_formats:
            image_file: str = intro_page.replace('.md', fmt)
            if os.path.exists(image_file):
                image = image_file
                break
        if os.path.exists(intro_page):
            with open(intro_page, 'r', encoding='utf-8') as f:
                content = md2html(f.read())
        out_file.write(template.render(title='Cyberpunk 2025', content=content, image=image,
                                       **parse_options(intro_page)))


def main() -> None:
    global md_pages, html_pages
    md_pages = sorted(
        set(os.path.relpath(os.path.join(root, file))
            for root, _, files in os.walk(desc_path)
            for file in files if file.endswith('.md')) - {intro_page},
        key=get_page_sort_key
    )
    html_pages = list(map(lambda name: name.replace('.md', '.html'), md_pages))
    clean()
    with open('template.jinja', 'r', encoding='utf-8') as t:
        insert_properties(default_options)
        template: j2.Template = j2.Template(t.read())
        template.globals.update(pages=html_pages, get_page_title=get_page_title,
                                get_page_group=get_page_group, group_diff=group_diff, len=len)
        generate_subsistes(template)
        generate_main(template)


if __name__ == '__main__':
    main()
