import os
import sqlite3
import hashlib
from pathlib import Path

import streamlit as st


# =========================================================
# 設定
# =========================================================

DB_PATH = "app.db"
IMAGE_DIR = Path("images")
IMAGE_DIR.mkdir(exist_ok=True)

# 管理者パスワード
# 本番運用ではコードに直接書かず、Streamlit secrets を使うのがおすすめです。
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "admin123")


# =========================================================
# ページ設定
# =========================================================

st.set_page_config(
    page_title="シナリオ・キャラクター一覧",
    page_icon="",
    layout="wide",
)


# =========================================================
# DB
# =========================================================

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # -----------------------------------------------------
    # シナリオ
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scenarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # -----------------------------------------------------
    # キャラクター
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS characters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scenario_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            player_name TEXT DEFAULT '',
            description TEXT DEFAULT '',
            image_path TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (scenario_id)
                REFERENCES scenarios(id)
                ON DELETE CASCADE
        )
    """)

    # -----------------------------------------------------
    # 既存DBに sort_order がない場合は追加
    # -----------------------------------------------------

    scenario_columns = {
        row["name"]
        for row in cursor.execute(
            "PRAGMA table_info(scenarios)"
        ).fetchall()
    }

    if "sort_order" not in scenario_columns:

        cursor.execute("""
            ALTER TABLE scenarios
            ADD COLUMN sort_order INTEGER DEFAULT 0
        """)

        # 現在のID順をそのまま初期の並び順にする
        existing_scenarios = cursor.execute("""
            SELECT id
            FROM scenarios
            ORDER BY id ASC
        """).fetchall()

        for index, scenario in enumerate(existing_scenarios):

            cursor.execute("""
                UPDATE scenarios
                SET sort_order = ?
                WHERE id = ?
            """, (
                index,
                scenario["id"],
            ))

    conn.commit()
    conn.close()


init_db()


# =========================================================
# 管理者認証
# =========================================================

def is_admin():
    return st.session_state.get("is_admin", False)


def admin_login():
    st.sidebar.markdown("###  管理者")

    if is_admin():
        st.sidebar.success("管理者としてログイン中")

        if st.sidebar.button("ログアウト"):
            st.session_state.is_admin = False
            st.rerun()

        return

    with st.sidebar.expander("管理者ログイン"):

        password = st.text_input(
            "パスワード",
            type="password",
            key="admin_password",
        )

        if st.button("ログイン"):

            if password == ADMIN_PASSWORD:
                st.session_state.is_admin = True
                st.rerun()

            else:
                st.error("パスワードが違います")


admin_login()


# =========================================================
# DB操作
# =========================================================

def get_scenarios():
    conn = get_connection()

    rows = conn.execute("""
        SELECT *
        FROM scenarios
        ORDER BY sort_order ASC, id ASC
    """).fetchall()

    conn.close()
    return rows


def get_scenario(scenario_id):
    conn = get_connection()

    row = conn.execute("""
        SELECT *
        FROM scenarios
        WHERE id = ?
    """, (scenario_id,)).fetchone()

    conn.close()
    return row


def get_characters(scenario_id):
    conn = get_connection()

    rows = conn.execute("""
        SELECT *
        FROM characters
        WHERE scenario_id = ?
        ORDER BY id ASC
    """, (scenario_id,)).fetchall()

    conn.close()
    return rows


def add_scenario(name, description):
    conn = get_connection()

    # 新しいシナリオは常に一覧の先頭に追加
    min_order = conn.execute("""
        SELECT COALESCE(MIN(sort_order), 0)
        FROM scenarios
    """).fetchone()[0]

    conn.execute("""
        INSERT INTO scenarios
        (
            name,
            description,
            sort_order
        )
        VALUES (?, ?, ?)
    """, (
        name,
        description,
        min_order - 1,
    ))

    conn.commit()
    conn.close()


def update_scenario(scenario_id, name, description):
    conn = get_connection()

    conn.execute("""
        UPDATE scenarios
        SET name = ?, description = ?
        WHERE id = ?
    """, (
        name,
        description,
        scenario_id,
    ))

    conn.commit()
    conn.close()


def move_scenario_up(scenario_id):
    scenarios = get_scenarios()

    current_index = None

    for index, scenario in enumerate(scenarios):

        if scenario["id"] == scenario_id:
            current_index = index
            break

    if current_index is None or current_index == 0:
        return

    current = scenarios[current_index]
    previous = scenarios[current_index - 1]

    conn = get_connection()

    conn.execute("""
        UPDATE scenarios
        SET sort_order = ?
        WHERE id = ?
    """, (
        previous["sort_order"],
        current["id"],
    ))

    conn.execute("""
        UPDATE scenarios
        SET sort_order = ?
        WHERE id = ?
    """, (
        current["sort_order"],
        previous["id"],
    ))

    conn.commit()
    conn.close()


def move_scenario_down(scenario_id):
    scenarios = get_scenarios()

    current_index = None

    for index, scenario in enumerate(scenarios):

        if scenario["id"] == scenario_id:
            current_index = index
            break

    if (
        current_index is None
        or current_index >= len(scenarios) - 1
    ):
        return

    current = scenarios[current_index]
    next_scenario = scenarios[current_index + 1]

    conn = get_connection()

    conn.execute("""
        UPDATE scenarios
        SET sort_order = ?
        WHERE id = ?
    """, (
        next_scenario["sort_order"],
        current["id"],
    ))

    conn.execute("""
        UPDATE scenarios
        SET sort_order = ?
        WHERE id = ?
    """, (
        current["sort_order"],
        next_scenario["id"],
    ))

    conn.commit()
    conn.close()


def add_character(
    scenario_id,
    name,
    player_name,
    description,
    image_path,
):
    conn = get_connection()

    conn.execute("""
        INSERT INTO characters
        (
            scenario_id,
            name,
            player_name,
            description,
            image_path
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        scenario_id,
        name,
        player_name,
        description,
        image_path,
    ))

    conn.commit()
    conn.close()


def delete_character(character_id):
    conn = get_connection()

    row = conn.execute("""
        SELECT image_path
        FROM characters
        WHERE id = ?
    """, (character_id,)).fetchone()

    if row and row["image_path"]:

        image_path = row["image_path"]

        # URLの場合は削除しない
        if not (
            image_path.startswith("http://")
            or image_path.startswith("https://")
        ):

            path = Path(image_path)

            if path.exists():
                path.unlink()

    conn.execute("""
        DELETE FROM characters
        WHERE id = ?
    """, (character_id,))

    conn.commit()
    conn.close()


def delete_scenario(scenario_id):
    conn = get_connection()

    characters = conn.execute("""
        SELECT image_path
        FROM characters
        WHERE scenario_id = ?
    """, (scenario_id,)).fetchall()

    for character in characters:

        image_path = character["image_path"]

        if not image_path:
            continue

        # ココフォリアなどのURLは削除しない
        if (
            image_path.startswith("http://")
            or image_path.startswith("https://")
        ):
            continue

        path = Path(image_path)

        if path.exists():
            path.unlink()

    conn.execute("""
        DELETE FROM characters
        WHERE scenario_id = ?
    """, (scenario_id,))

    conn.execute("""
        DELETE FROM scenarios
        WHERE id = ?
    """, (scenario_id,))

    conn.commit()
    conn.close()


# =========================================================
# 画像保存
# =========================================================

def save_uploaded_image(uploaded_file):

    if uploaded_file is None:
        return ""

    original_name = Path(
        uploaded_file.name
    ).name

    extension = Path(
        original_name
    ).suffix.lower()

    allowed_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
    }

    if extension not in allowed_extensions:
        st.error(
            "対応していない画像形式です。"
        )
        return ""

    file_hash = hashlib.md5(
        uploaded_file.getvalue()
    ).hexdigest()[:12]

    filename = (
        f"{file_hash}{extension}"
    )

    save_path = IMAGE_DIR / filename

    with open(save_path, "wb") as f:
        f.write(
            uploaded_file.getbuffer()
        )

    return str(save_path)


def display_character_image(

    image_path,

    width=None,

):

    if not image_path:

        st.write("️")

        return

    # ココフォリア等のURL

    if (

        image_path.startswith("http://")

        or image_path.startswith("https://")

    ):

        if width:

            st.image(

                image_path,

                width=width,

            )

        else:

            st.image(

                image_path,

                use_container_width=True,

            )

        return

    # アップロード画像

    path = Path(image_path)

    if path.exists():

        if width:

            st.image(

                image_path,

                width=width,

            )

        else:

            st.image(

                image_path,

                use_container_width=True,

            )

    else:

        st.write("️")

# =========================================================

# セッション状態

# =========================================================

if "selected_scenario_id" not in st.session_state:

    st.session_state.selected_scenario_id = None

# =========================================================

# 管理画面

# =========================================================

def admin_page():

    st.title("️ 管理画面")

    tab1, tab2, tab3 = st.tabs([

        "シナリオ追加",

        "キャラクター追加",

        "管理・削除",

    ])

    # =====================================================

    # シナリオ追加

    # =====================================================

    with tab1:

        st.subheader(

            "新しいシナリオを追加"

        )

        with st.form(

            "add_scenario_form"

        ):

            name = st.text_input(

                "シナリオ名",

                placeholder="例：■■が消えた夏",

            )

            description = st.text_area(

                "説明",

                placeholder="シナリオについての説明",

            )

            submitted = st.form_submit_button(

                "シナリオを追加"

            )

            if submitted:

                if not name.strip():

                    st.error(

                        "シナリオ名を入力してください。"

                    )

                else:

                    add_scenario(

                        name.strip(),

                        description.strip(),

                    )

                    st.success(

                        "シナリオを追加しました。"

                    )

                    st.rerun()

    # =====================================================

    # キャラクター追加

    # =====================================================

    with tab2:

        st.subheader(

            "キャラクターを追加"

        )

        scenarios = get_scenarios()

        if not scenarios:

            st.info(

                "先にシナリオを追加してください。"

            )

        else:

            scenario_options = {

                scenario["name"]: scenario["id"]

                for scenario in scenarios

            }

            selected_name = st.selectbox(

                "参加シナリオ",

                list(

                    scenario_options.keys()

                ),

            )

            selected_id = scenario_options[

                selected_name

            ]

            with st.form(

                "add_character_form"

            ):

                character_name = st.text_input(

                    "キャラクター名",

                    placeholder="例：山田 太郎",

                )

                player_name = st.text_input(

                    "PL名",

                    placeholder="例：〇〇さん",

                )

                description = st.text_area(

                    "キャラクター説明",

                    placeholder="キャラクターについてのメモ",

                )

                # -------------------------------------------------

                # 画像

                # -------------------------------------------------

                st.markdown("#### キャラクター画像")

                image_source = st.radio(

                    "画像の取得方法",

                    [

                        "画像をアップロード",

                        "ココフォリアの画像URLを使用",

                    ],

                    horizontal=True,

                )

                uploaded_image = None

                cocofolia_image_url = ""

                if image_source == "画像をアップロード":

                    uploaded_image = st.file_uploader(

                        "キャラクター画像",

                        type=[

                            "jpg",

                            "jpeg",

                            "png",

                            "webp",

                        ],

                    )

                else:

                    cocofolia_image_url = st.text_input(

                        "ココフォリアの画像URL",

                        placeholder=(

                            "https://image.iaproject.app/..."

                        ),

                    )

                submitted = st.form_submit_button(

                    "キャラクターを追加"

                )

                if submitted:

                    if not character_name.strip():

                        st.error(

                            "キャラクター名を入力してください。"

                        )

                    else:

                        # -----------------------------

                        # アップロード画像

                        # -----------------------------

                        image_path = ""

                        if image_source == "画像をアップロード":

                            image_path = (

                                save_uploaded_image(

                                    uploaded_image

                                )

                            )

                        # -----------------------------

                        # ココフォリア画像URL

                        # -----------------------------

                        else:

                            image_path = (

                                cocofolia_image_url.strip()

                            )

                            if image_path:

                                if not (

                                    image_path.startswith(

                                        "http://"

                                    )

                                    or image_path.startswith(

                                        "https://"

                                    )

                                ):

                                    st.error(

                                        "画像URLが正しくありません。"

                                        "https:// から始まるURLを入力してください。"

                                    )

                                    st.stop()

                        # -----------------------------

                        # DBへ保存

                        # -----------------------------

                        add_character(

                            selected_id,

                            character_name.strip(),

                            player_name.strip(),

                            description.strip(),

                            image_path,

                        )

                        st.success(

                            "キャラクターを追加しました。"

                        )

                        st.rerun()

    # =====================================================

    # 管理・削除

    # =====================================================

    with tab3:

        st.subheader(

            "データ管理"

        )

        scenarios = get_scenarios()

        if not scenarios:

            st.info(

                "まだシナリオがありません。"

            )

            return

        for scenario in scenarios:

            with st.expander(

                f" {scenario['name']}"

            ):

                st.write(

                    scenario["description"]

                    or "説明なし"

                )

                # -------------------------------------------------

                # 並び替え

                # -------------------------------------------------

                st.markdown(

                    "#### シナリオの順番"

                )

                move_col1, move_col2 = st.columns(2)

                scenario_index = next(

                    (

                        i

                        for i, s in enumerate(scenarios)

                        if s["id"] == scenario["id"]

                    ),

                    0,

                )

                with move_col1:

                    if st.button(

                        "↑ 上へ",

                        key=f"move_up_{scenario['id']}",

                        disabled=(

                            scenario_index == 0

                        ),

                        use_container_width=True,

                    ):

                        move_scenario_up(

                            scenario["id"]

                        )

                        st.rerun()

                with move_col2:

                    if st.button(

                        "↓ 下へ",

                        key=f"move_down_{scenario['id']}",

                        disabled=(

                            scenario_index

                            == len(scenarios) - 1

                        ),

                        use_container_width=True,

                    ):

                        move_scenario_down(

                            scenario["id"]

                        )

                        st.rerun()

                st.markdown("---")

                # -------------------------------------------------

                # 編集・削除

                # -------------------------------------------------

                col1, col2 = st.columns(2)

                with col1:

                    st.markdown(
                        
                               "#### 編集"

                    )

                    edit_name = st.text_input(

                        "シナリオ名",

                        value=scenario["name"],

                        key=f"name_{scenario['id']}",

                    )

                    edit_description = st.text_area(

                        "説明",

                        value=scenario["description"],

                        key=(

                            f"description_"

                            f"{scenario['id']}"

                        ),

                    )

                    if st.button(

                        "変更を保存",

                        key=f"save_{scenario['id']}",

                    ):

                        update_scenario(

                            scenario["id"],

                            edit_name,

                            edit_description,

                        )

                        st.success(

                            "保存しました。"

                        )

                        st.rerun()

                with col2:

                    st.markdown(

                        "#### 削除"

                    )

                    st.warning(

                        "シナリオを削除すると、"

                        "参加キャラクターも削除されます。"

                    )

                    if st.button(

                        "このシナリオを削除",

                        key=(

                            f"delete_"

                            f"{scenario['id']}"

                        ),

                    ):

                        delete_scenario(

                            scenario["id"]

                        )

                        st.success(

                            "削除しました。"

                        )

                        st.rerun()

                st.markdown("---")

                # -------------------------------------------------

                # 登録キャラクター

                # -------------------------------------------------

                st.markdown(

                    "#### 登録されているキャラクター"

                )

                characters = get_characters(

                    scenario["id"]

                )

                if not characters:

                    st.info(

                        "キャラクターはいません。"

                    )

                else:

                    for character in characters:

                        col1, col2 = st.columns(

                            [1, 4]

                        )

                        with col1:

                            display_character_image(

                                character["image_path"],

                                width=120,

                            )

                        with col2:

                            st.write(

                                f"**{character['name']}**"

                            )

                            if character["player_name"]:

                                st.write(

                                    "PL："

                                    f"{character['player_name']}"

                                )

                            if character["description"]:

                                st.write(

                                    character["description"]

                                )

                            if st.button(

                                "キャラクターを削除",

                                key=(

                                    f"delete_character_"

                                    f"{character['id']}"

                                ),

                            ):

                                delete_character(

                                    character["id"]

                                )

                                st.success(

                                    "削除しました。"

                                )

                                st.rerun()

# =========================================================

# メイン画面

# =========================================================

def main_page():

    # =====================================================

    # シナリオ詳細

    # =====================================================

    if st.session_state.selected_scenario_id:

        scenario = get_scenario(

            st.session_state.selected_scenario_id

        )

        if scenario is None:

            st.session_state.selected_scenario_id = None

            st.rerun()

        if st.button(

            "← シナリオ一覧に戻る"

        ):

            st.session_state.selected_scenario_id = None

            st.rerun()

        st.title(

            scenario["name"]

        )

        if scenario["description"]:

            st.write(

                scenario["description"]

            )

        st.divider()

        st.subheader(

            "参加キャラクター"

        )

        characters = get_characters(

            scenario["id"]

        )

        if not characters:

            st.info(

                "このシナリオに登録されている"

                "キャラクターはいません。"

            )

            return

        columns = st.columns(3)

        for index, character in enumerate(

            characters

        ):

            with columns[index % 3]:

                display_character_image(

                    character["image_path"]

                )

                st.markdown(

                    f"### {character['name']}"

                )

                if character["player_name"]:

                    st.caption(

                        "PL："

                        f"{character['player_name']}"

                    )

                if character["description"]:

                    st.write(

                        character["description"]

                    )

                st.divider()

        return

    # =====================================================

    # シナリオ一覧

    # =====================================================

    st.title(

        " シナリオ一覧"

    )

    st.write(

        "シナリオを選択すると、"

        "参加したキャラクターを見ることができます。"

    )

    st.divider()

    scenarios = get_scenarios()

    sort_direction = st.radio(
        "並び順",
        ["古い順", "新しい順"],
        horizontal=True,
        index=0,
    )

    if sort_direction == "昇順":
        scenarios = list(reversed(scenarios))

    if not scenarios:

        st.info(

            "まだシナリオが登録されていません。"

        )

        return

    for scenario in scenarios:

        if st.button(

            f"・{scenario['name']}",

            key=f"scenario_{scenario['id']}",

            use_container_width=True,

        ):

            st.session_state.selected_scenario_id = (

                scenario["id"]

            )

            st.rerun()

# =========================================================

# サイドバー

# =========================================================

st.sidebar.markdown("---")

if is_admin():

    page = st.sidebar.radio(

        "ページ",

        [

            "シナリオ一覧",

            "管理画面",

        ],

    )

else:

    page = "シナリオ一覧"

# =========================================================

# 表示

# =========================================================

if page == "管理画面" and is_admin():

    admin_page()

else:

    main_page()
