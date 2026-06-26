let characters = [];
let filteredCharacters = [];

const grid = document.getElementById("characterGrid");
const searchBox = document.getElementById("searchBox");
const categoryButtons = document.querySelectorAll(".category");

let currentCategory = "all";

// =========================
// characters.json を読み込む
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
// キャラクター一覧表示
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
                <img src="${character.image}" alt="${character.name}">
            </div>

            <div class="character-info">

                <div class="character-name">
                    ${character.name}
                </div>

                <div class="character-category">
                    ${character.category}
                </div>

                <div class="character-text">
                    ${character.description}
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
// 検索
// =========================

searchBox.addEventListener("input", filterCharacters);


// =========================
// カテゴリー
// =========================

categoryButtons.forEach(button => {

    button.addEventListener("click", () => {

        categoryButtons.forEach(btn => {
            btn.classList.remove("active");
        });

        button.classList.add("active");

        currentCategory = button.dataset.category;

        filterCharacters();

    });

});


// =========================
// 検索・絞り込み
// =========================

function filterCharacters() {

    const keyword = searchBox.value.toLowerCase();

    filteredCharacters = characters.filter(character => {

        const matchName =
            character.name.toLowerCase().includes(keyword);

        const matchCategory =
            currentCategory === "all" ||
            character.category === currentCategory;

        return matchName && matchCategory;

    });

    displayCharacters(filteredCharacters);

}