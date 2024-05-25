// Copyright (c) 2024 iiPython
const pages = [%s];
const length = location.origin.length;
const cache = {};
const replace = document.querySelector("%s");
for (const link of document.getElementsByTagName("a")) {
    const relative = link.href.slice(length);
    if (!pages.includes(relative)) continue;
    link.addEventListener("click", async (e) => {
        e.preventDefault();
        if (!cache[relative]) cache[relative] = await (await fetch(`/pages${relative === '/' ? '/index' : relative}`)).text();
        const title = relative.slice(1);
        document.title = `%s${title && ('%s' + title[0].toUpperCase() + title.slice(1))}`;
        replace.innerHTML = "";
        replace.append(document.createRange().createContextualFragment(cache[relative]));
        history.pushState(null, document.title, relative);
    });
}