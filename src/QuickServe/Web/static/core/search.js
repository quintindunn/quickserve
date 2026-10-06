const search_bar = document.getElementById("search-bar");
const search_endpoint = document.getElementById("search-endpoint").value;

search_bar.addEventListener("keydown", (e) => {
    if (e.key !== "Enter") { return; }

    const xhr = new XMLHttpRequest();
    const url = new URL(search_endpoint, window.location.origin);

    url.searchParams.set("query", search_bar.value);

    xhr.open("GET", url, true);
    xhr.setRequestHeader("Accept", "application/xml");

    xhr.onload = function () {
        if (xhr.status >= 200 && xhr.status < 300) {
            const xml = xhr.responseText;
            console.log(xml);
        }
    };

    xhr.onerror = function () {
        console.error("Request failed");
    };

    xhr.send();
})