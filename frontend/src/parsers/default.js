export const defaultParser = (htmlString) => {
    const parser = new DOMParser()
    const doc = parser.parseFromString(htmlString, "text/html")

    // Simple default: Get all links that look like they might be events
    const links = Array.from(doc.querySelectorAll("a"))
        .filter((a) => a.href && (a.href.includes("event") || a.textContent.toLowerCase().includes("rsvp")))
        .map((a) => ({
            title: a.textContent.trim() || "Event Link",
            url: a.href,
            date: null,
        }))

    return Array.from(new Map(links.map((e) => [e.url, e])).values())
}
