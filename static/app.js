const searchForm =
    document.getElementById("searchForm");

const queryInput =
    document.getElementById("queryInput");

const topK =
    document.getElementById("topK");

const searchButton =
    document.getElementById("searchButton");

const statusBox =
    document.getElementById("status");

const resultTitle =
    document.getElementById("resultTitle");

const resultCount =
    document.getElementById("resultCount");

const resultsGrid =
    document.getElementById("resultsGrid");


function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


function formatTimestamp(seconds) {
    if (
        seconds === null
        || seconds === undefined
    ) {
        return "";
    }

    const total =
        Math.max(
            Math.round(Number(seconds)),
            0
        );

    const hours =
        Math.floor(total / 3600);

    const minutes =
        Math.floor((total % 3600) / 60);

    const secs =
        total % 60;

    if (hours > 0) {
        return [hours, minutes, secs]
            .map(value =>
                String(value).padStart(2, "0")
            )
            .join(":");
    }

    return [minutes, secs]
        .map(value =>
            String(value).padStart(2, "0")
        )
        .join(":");
}


function renderResults(results) {
    if (!results.length) {
        resultsGrid.innerHTML = `
            <div class="empty">
                Không tìm thấy dữ liệu phù hợp.
            </div>
        `;

        return;
    }

    resultsGrid.innerHTML =
        results.map(item => {
            const title =
                escapeHtml(
                    item.title || "Không có tiêu đề"
                );

            const mediaUrl =
                escapeHtml(item.media_url);

            const score =
                (
                    Number(item.score) * 100
                ).toFixed(1);

            const timestamp =
                formatTimestamp(
                    item.best_timestamp_seconds
                );

            let preview = "";

            if (item.media_type === "video") {
                preview = `
                    <video
                        src="${mediaUrl}"
                        controls
                        preload="metadata"
                        data-start-time="${
                            item.best_timestamp_seconds ?? 0
                        }"
                    ></video>

                    ${
                        timestamp
                            ? `
                                <span class="timestamp">
                                    Khớp nhất: ${timestamp}
                                </span>
                            `
                            : ""
                    }
                `;
            } else {
                preview = `
                    <img
                        src="${mediaUrl}"
                        alt="${title}"
                        loading="lazy"
                    >
                `;
            }

            return `
                <article class="media-card">
                    <div class="media-preview">
                        ${preview}
                    </div>

                    <div class="media-info">
                        <h3 class="media-title">
                            ${title}
                        </h3>

                        <div class="media-meta">
                            <span>
                                ${
                                    item.media_type === "video"
                                        ? "Video"
                                        : "Ảnh"
                                }
                            </span>

                            <span class="score">
                                ${score}%
                            </span>
                        </div>
                    </div>
                </article>
            `;
        })
        .join("");

    document
        .querySelectorAll(
            "video[data-start-time]"
        )
        .forEach(video => {
            video.addEventListener(
                "loadedmetadata",
                () => {
                    const startTime =
                        Number(
                            video.dataset.startTime || 0
                        );

                    if (
                        startTime > 0
                        && startTime < video.duration
                    ) {
                        video.currentTime = startTime;
                    }
                },
                { once: true }
            );
        });
}


searchForm.addEventListener(
    "submit",
    async event => {
        event.preventDefault();

        const query =
            queryInput.value.trim();

        if (!query) {
            return;
        }

        searchButton.disabled = true;

        statusBox.textContent =
            "Đang tìm kiếm dữ liệu...";

        resultTitle.textContent =
            `Đang tìm: “${query}”`;

        resultCount.textContent = "...";

        try {
            const url =
                `/api/search?q=${
                    encodeURIComponent(query)
                }&top_k=${
                    encodeURIComponent(topK.value)
                }`;

            const response =
                await fetch(url);

            const data =
                await response.json();

            if (!response.ok) {
                throw new Error(
                    data.detail
                    || "Không thể tìm kiếm."
                );
            }

            renderResults(data.results);

            resultTitle.textContent =
                `Kết quả cho: “${data.query}”`;

            resultCount.textContent =
                data.count;

            statusBox.textContent =
                `Đã tìm thấy ${data.count} kết quả.`;

        } catch (error) {
            resultsGrid.innerHTML = `
                <div class="empty">
                    ${escapeHtml(error.message)}
                </div>
            `;

            resultTitle.textContent =
                "Tìm kiếm thất bại";

            resultCount.textContent = "0";

            statusBox.textContent =
                `Lỗi: ${error.message}`;

        } finally {
            searchButton.disabled = false;
        }
    }
);