let characters = [];
let filteredCharacters = [];

const grid = document.getElementById("characterGrid");
const searchBox = document.getElementById("searchBox");

let currentCategory = "all";


// =========================
// JSON読み込み
// =========================

fetch("characters.json")
    .then(response => response.json())
    .then(data => {

        characters = data;
        filteredCharacters = data;

        displayCharacters(filteredCharacters);

    })
    .catch(error => {

        console.error("JSONの読み込みに失敗しました", error);

        grid.innerHTML = `
            <h2 style="text-align:center;">
                characters.json が読み込めませんでした
            </h2>
        `;
    });


// =========================
// 一覧表示
// =========================

function displayCharacters(list) {

    grid.innerHTML = "";

    if (list.length === 0) {

        grid.innerHTML = `
            <h2 style="text-align:center;width:100%;">
                キャラクターが見つかりません
            </h2>
        `;

        return;
    }

    list.forEach(character => {

        const card = document.createElement("div");
        card.className = "character-card";

        card.innerHTML = `
            <div class="character-image">
                <img src="${character.thumb}" alt="${character.name}">
            </div>

            <div class="character-info">

                <div class="character-name">
                    ${character.name}
                </div>

                <div class="character-kana">
                    ${character.kana}
                </div>

                <div class="character-job">
                    ${character.job}
                </div>


                <div class="character-likes">
                    好きなもの：${character.likes}
                </div>


            </div>
        `;

        card.addEventListener("click", () => {
            location.href = `character.html?id=${character.id}`;
        });

        grid.appendChild(card);

    });
}


// =========================
// 検索（名前＋かな対応）
// =========================

searchBox.addEventListener("input", filterCharacters);

function filterCharacters() {

    const keyword = searchBox.value.toLowerCase();

    filteredCharacters = characters.filter(character => {

        const matchName =
            character.name.toLowerCase().includes(keyword);

        const matchKana =
            character.kana.toLowerCase().includes(keyword);

        const matchProfile =
            character.profile.toLowerCase().includes(keyword);

        const matchJob =
            character.job.toLowerCase().includes(keyword);

        const matchStory =
            character.story.toLowerCase().includes(keyword);

        return (
            matchName ||
            matchKana ||
            matchProfile ||
            matchJob ||
            matchStory
        );
    });

    displayCharacters(filteredCharacters);
}
