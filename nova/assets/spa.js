// Copyright (c) 2024 iiPython
const pages = [%s];
const length = location.origin.length;
const cache = {};
const replace = document.querySelector("%s");
for (const link of document.getElementsByTagName("a")) {
    const relative = link.href.slice(length);
    if (!pages.includes(relative)) continue;
    const load_page = async () => {
        cache[relative] = await (await fetch(`/pages${relative === '/' ? '/index' : relative}`)).text();
    }
    const handle_hover = () => {
        if (cache[relative]) return;
        load_page()
        removeEventListener("mouseover", handle_hover);
    }
    link.addEventListener("mouseover", handle_hover);
    link.addEventListener("click", (e) => {
        e.preventDefault();
        if (!cache[relative]) load_page();
        const title = relative.slice(1);
        document.title = `%s${title && ('%s' + title[0].toUpperCase() + title.slice(1))}`;
        replace.innerHTML = "";
        replace.append(document.createRange().createContextualFragment(cache[relative]));
        history.pushState(null, document.title, relative);
    });
}