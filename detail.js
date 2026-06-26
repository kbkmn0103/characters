// ======================================
// URLからIDを取得
// ======================================

const params = new URLSearchParams(window.location.search);

const id = Number(params.get("id"));


// ======================================
// JSONを読み込む
// ======================================

fetch("characters.json")
    .then(response => response.json())
    .then(characters => {

        const character = characters.find(c => c.id === id);

        if (!character) {

            document.body.innerHTML = `
                <h1 style="text-align:center;margin-top:80px;">
                    キャラクターが見つかりません
                </h1>
            `;

            return;
        }

        showCharacter(character);

    });


// ======================================
// 表示
// ======================================

function showCharacter(character){

    document.getElementById("detailImage").src =
        character.image;

    document.getElementById("detailImage").alt =
        character.name;

    document.getElementById("detailName").textContent =
        character.name;

    document.getElementById("detailCategory").textContent =
        character.category;

    document.getElementById("detailBirthday").textContent =
        character.birthday;

    document.getElementById("detailLikes").textContent =
        character.likes;

    document.getElementById("detailPersonality").textContent =
        character.personality;

    document.getElementById("detailProfile").textContent =
        character.profile;

}