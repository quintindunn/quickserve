const search_bar = document.getElementById("search-bar");
const search_endpoint = document.getElementById("search-endpoint").value;
const search_results = document.getElementById("search-results");

search_bar.addEventListener("input", () => {
    const query = search_bar.value.trim();

    if (!query) {
        search_results.innerHTML = "";
        search_results.dataset.shown = "false";
        return;
    }

    const xhr = new XMLHttpRequest();
    const url = new URL(search_endpoint, window.location.origin);

    url.searchParams.set("query", query);

    xhr.open("GET", url, true);
    xhr.setRequestHeader("Accept", "application/xml");

    xhr.onload = function () {
        if (xhr.status >= 200 && xhr.status < 300 && xhr.status !== 204) {
            search_results.innerHTML = xhr.responseText;
            search_results.dataset.shown = "true";
        }
        if (xhr.status === 204) {
            search_results.dataset.shown = "false";
        }
    };

    xhr.onerror = function () {
        console.error("Request failed");
    };

    xhr.send();
});

document.addEventListener("click", (e) => {
    if (!search_bar.contains(e.target) && !search_results.contains(e.target)) {
        search_results.dataset.shown = "false";
    } else {
        const query = search_bar.value.trim();
        if (query !== "") {
            search_results.dataset.shown = "true";
        }
    }
});