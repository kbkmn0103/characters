//=====================================
// URLからID取得
//=====================================

const params = new URLSearchParams(window.location.search);

const id = Number(params.get("id"));


//=====================================
// JSON読込
//=====================================

fetch("characters.json")

.then(response=>response.json())

.then(characters=>{

    const character=

    characters.find(c=>c.id===id);

    if(!character){

        document.body.innerHTML=`

        <h1 style="color:white;text-align:center;margin-top:150px;">

        FILE NOT FOUND

        </h1>

        `;

        return;

    }

    loadCharacter(character);

});


//=====================================
// 表示
//=====================================

function loadCharacter(character){

    document.title=

    character.name+" | Character Archive";


    document.querySelector(".report-code").textContent=

    "CASE-"+String(character.id).padStart(3,"0");


    document.getElementById("detailName").textContent=

    character.name;


    document.getElementById("detailKana").textContent=

    character.kana;


    document.getElementById("detailImage").src=

    character.image;


    document.getElementById("detailBirthday").textContent=

    character.birthday;


    document.getElementById("detailAge").textContent=

    character.age;


    document.getElementById("detailHeight").textContent=

    character.height;


    document.getElementById("detailOccupation").textContent=

    character.occupation;


    document.getElementById("detailLikes").textContent=

    character.likes;


    document.getElementById("detailDislikes").textContent=

    character.dislikes;


    document.getElementById("detailProfile").textContent=

    character.profile;


    document.getElementById("detailMemo").textContent=

    character.memo;

}