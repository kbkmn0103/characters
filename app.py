import os
import sqlite3
import hashlib
from pathlib import Path

import streamlit as st

def add_character_to_db(
    scenario_id,
    character,
):
    conn = get_connection()

    conn.execute("""
        INSERT INTO characters (
            scenario_id,
            name,
            external_url,
            image_path,
            hp,
            mp,
            san,
            luck,
            str,
            con,
            pow,
            dex,
            app,
            siz,
            int,
            edu
        )
        VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?
        )
    """, (
        scenario_id,
        character["name"],
        character["external_url"],
        character["icon_url"],  # ひとまず画像URLを保存
        character["hp"],
        character["mp"],
        character["san"],
        character["luck"],
        character["str"],
        character["con"],
        character["pow"],
        character["dex"],
        character["app"],
        character["siz"],
        character["int"],
        character["edu"],
    ))

    conn.commit()
    conn.close()
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
    page_icon="📚",
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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scenarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS characters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scenario_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            external_url TEXT DEFAULT '',
            image_path TEXT DEFAULT '',
            hp TEXT DEFAULT '',
            mp TEXT DEFAULT '',
            san TEXT DEFAULT '',
            luck TEXT DEFAULT '',
            str TEXT DEFAULT '',
            con TEXT DEFAULT '',
            pow TEXT DEFAULT '',
            dex TEXT DEFAULT '',
            app TEXT DEFAULT '',
            siz TEXT DEFAULT '',
            int TEXT DEFAULT '',
            edu TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (scenario_id)
                REFERENCES scenarios(id)
        )
    """)

    conn.commit()
    conn.close()


init_db()

import json


def parse_character_data(text):
    raw = json.loads(text)

    data = raw["data"]

    # ステータス
    status = {
        item["label"]: item["value"]
        for item in data.get("status", [])
    }

    # 能力値
    params = {
        item["label"]: item["value"]
        for item in data.get("params", [])
    }

    return {
        "name": data.get("name", ""),
        "icon_url": data.get("iconUrl", ""),
        "external_url": data.get("externalUrl", ""),

        "hp": status.get("HP", ""),
        "mp": status.get("MP", ""),
        "san": status.get("SAN", ""),
        "luck": status.get("幸運", ""),

        "str": params.get("STR", ""),
        "con": params.get("CON", ""),
        "pow": params.get("POW", ""),
        "dex": params.get("DEX", ""),
        "app": params.get("APP", ""),
        "siz": params.get("SIZ", ""),
        "int": params.get("INT", ""),
        "edu": params.get("EDU", ""),
    }
# =========================================================
# 管理者認証
# =========================================================

def is_admin():
    return st.session_state.get("is_admin", False)


def admin_login():
    st.sidebar.markdown("### 🔐 管理者")

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
        ORDER BY id ASC
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

    conn.execute("""
        INSERT INTO scenarios (name, description)
        VALUES (?, ?)
    """, (name, description))

    conn.commit()
    conn.close()


def update_scenario(scenario_id, name, description):
    conn = get_connection()

    conn.execute("""
        UPDATE scenarios
        SET name = ?, description = ?
        WHERE id = ?
    """, (name, description, scenario_id))

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
        image_path = Path(row["image_path"])

        if image_path.exists():
            image_path.unlink()

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
        if character["image_path"]:
            image_path = Path(character["image_path"])

            if image_path.exists():
                image_path.unlink()

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

    # ファイル名を安全にする
    original_name = Path(uploaded_file.name).name

    # 拡張子
    extension = Path(original_name).suffix.lower()

    allowed_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
    }

    if extension not in allowed_extensions:
        st.error("対応していない画像形式です。")
        return ""

    # ファイル名衝突を避ける
    file_hash = hashlib.md5(
        uploaded_file.getvalue()
    ).hexdigest()[:12]

    filename = f"{file_hash}{extension}"
    save_path = IMAGE_DIR / filename

    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return str(save_path)


# =========================================================
# セッション状態
# =========================================================

if "selected_scenario_id" not in st.session_state:
    st.session_state.selected_scenario_id = None


# =========================================================
# 管理画面
# =========================================================

def admin_page():
    st.title("⚙️ 管理画面")

    tab1, tab2, tab3 = st.tabs([
        "シナリオ追加",
        "キャラクター追加",
        "管理・削除",
    ])

    # -----------------------------------------------------
    # シナリオ追加
    # -----------------------------------------------------

    with tab1:
        st.subheader("新しいシナリオを追加")

        with st.form("add_scenario_form"):
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
                    st.error("シナリオ名を入力してください。")
                else:
                    add_scenario(
                        name.strip(),
                        description.strip(),
                    )

                    st.success("シナリオを追加しました。")
                    st.rerun()

    # -----------------------------------------------------
    # キャラクター追加
    # -----------------------------------------------------

    with tab2:
        st.subheader("キャラクター追加")
        
        scenarios = get_scenarios()
        
        if not scenarios:
            st.info("先にシナリオを追加してください。")
        
        else:
            scenario_names = [
                scenario["name"]
                for scenario in scenarios
            ]
        
            selected_name = st.selectbox(
                "参加シナリオ",
                scenario_names,
            )
        
            selected_scenario = next(
                scenario
                for scenario in scenarios
                if scenario["name"] == selected_name
            )
        
            st.markdown(
                "### ココフォリア等からコマデータを貼り付け"
            )
        
            character_json = st.text_area(
                "コマデータ",
                height=250,
                placeholder='{"kind":"character","data":{...}}',
                label_visibility="collapsed",
            )
        
            if st.button("データを読み込む"):
        
                try:
                    parsed = parse_character_data(
                        character_json
                    )
        
                    st.session_state.parsed_character = parsed
        
                    st.success("データを読み込みました！")
        
                except Exception as e:
                    st.error(f"データを読み込めませんでした: {e}")
            if st.session_state.get("parsed_character"):
            
                character = st.session_state.parsed_character
            
                st.divider()
            
                st.subheader("↓ 自動取得")
            
                st.markdown(
                    f"### 名前\n{character['name']}"
                )
            
                if character["icon_url"]:
                    st.image(
                        character["icon_url"],
                        width=200,
                    )
            
                if character["external_url"]:
                    st.link_button(
                        "キャラクターシートを開く",
                        character["external_url"],
                    )
            
                st.markdown("### ステータス")
            
                col1, col2, col3 = st.columns(3)
            
                with col1:
                    st.metric("HP", character["hp"] or "-")
            
                with col2:
                    st.metric("MP", character["mp"] or "-")
            
                with col3:
                    st.metric("SAN", character["san"] or "-")
            
                st.markdown("### 能力値")
            
                stats = [
                    ("STR", character["str"]),
                    ("CON", character["con"]),
                    ("POW", character["pow"]),
                    ("DEX", character["dex"]),
                    ("APP", character["app"]),
                    ("SIZ", character["siz"]),
                    ("INT", character["int"]),
                    ("EDU", character["edu"]),
                ]
            
                cols = st.columns(4)
            
                for i, (label, value) in enumerate(stats):
            
                    with cols[i % 4]:
                        st.metric(
                            label,
                            value or "-"
                        )
            
                st.divider()
            
                if st.button(
                    "このキャラクターを追加",
                    type="primary",
                    use_container_width=True,
                ):
                    # ↓ ここでDBに保存
                    add_character_to_db(
                        selected_scenario["id"],
                        character,
                    )
            
                    st.session_state.parsed_character = None
            
                    st.success(
                        "キャラクターを追加しました！"
                    )
            
                    st.rerun()
    # -----------------------------------------------------
    # 管理・削除
    # -----------------------------------------------------

    with tab3:
        st.subheader("データ管理")

        scenarios = get_scenarios()

        if not scenarios:
            st.info("まだシナリオがありません。")
            return

        for scenario in scenarios:
            with st.expander(
                f"📖 {scenario['name']}"
            ):
                st.write(
                    scenario["description"]
                    or "説明なし"
                )

                col1, col2 = st.columns(2)

                # 編集
                with col1:
                    st.markdown("#### 編集")

                    edit_name = st.text_input(
                        "シナリオ名",
                        value=scenario["name"],
                        key=f"name_{scenario['id']}",
                    )

                    edit_description = st.text_area(
                        "説明",
                        value=scenario["description"],
                        key=f"description_{scenario['id']}",
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

                        st.success("保存しました。")
                        st.rerun()

                # 削除
                with col2:
                    st.markdown("#### 削除")

                    st.warning(
                        "シナリオを削除すると、"
                        "参加キャラクターも削除されます。"
                    )

                    if st.button(
                        "このシナリオを削除",
                        key=f"delete_{scenario['id']}",
                    ):
                        delete_scenario(
                            scenario["id"]
                        )

                        st.success("削除しました。")
                        st.rerun()

                st.markdown("---")

                st.markdown("#### 登録されているキャラクター")

                characters = get_characters(
                    scenario["id"]
                )

                if not characters:
                    st.info("キャラクターはいません。")
                else:
                    for character in characters:
                        col1, col2 = st.columns(
                            [1, 4]
                        )

                        with col1:
                            if (
                                character["image_path"]
                                and Path(
                                    character["image_path"]
                                ).exists()
                            ):
                                st.image(
                                    character["image_path"],
                                    width=120,
                                )
                            else:
                                st.write("🖼️")

                        with col2:
                            st.write(
                                f"**{character['name']}**"
                            )

                            if character["player_name"]:
                                st.write(
                                    f"PL：{character['player_name']}"
                                )

                            if character["description"]:
                                st.write(
                                    character["description"]
                                )

                            if st.button(
                                "キャラクターを削除",
                                key=f"delete_character_{character['id']}",
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

    # -----------------------------------------------------
    # シナリオ詳細画面
    # -----------------------------------------------------

    if st.session_state.selected_scenario_id:

        scenario = get_scenario(
            st.session_state.selected_scenario_id
        )

        if scenario is None:
            st.session_state.selected_scenario_id = None
            st.rerun()

        if st.button("← シナリオ一覧に戻る"):
            st.session_state.selected_scenario_id = None
            st.rerun()

        st.title(scenario["name"])

        if scenario["description"]:
            st.write(scenario["description"])

        st.divider()

        st.subheader("参加キャラクター")

        characters = get_characters(
            scenario["id"]
        )

        if not characters:
            st.info(
                "このシナリオに登録されている"
                "キャラクターはいません。"
            )
            return

        # 3列表示
        columns = st.columns(3)

        for index, character in enumerate(characters):

            with columns[index % 3]:

                if (
                    character["image_path"]
                    and Path(
                        character["image_path"]
                    ).exists()
                ):
                    st.image(
                        character["image_path"],
                        use_container_width=True,
                    )
                else:
                    st.markdown(
                        "### 🖼️"
                    )

                st.markdown(
                    f"### {character['name']}"
                )

                if character["player_name"]:
                    st.caption(
                        f"PL：{character['player_name']}"
                    )

                if character["description"]:
                    st.write(
                        character["description"]
                    )

                st.divider()

        return

    # -----------------------------------------------------
    # シナリオ一覧
    # -----------------------------------------------------

    st.title("📚 シナリオ一覧")

    st.write(
        "シナリオを選択すると、"
        "参加したキャラクターを見ることができます。"
    )

    st.divider()

    scenarios = get_scenarios()

    if not scenarios:
        st.info(
            "まだシナリオが登録されていません。"
        )
        return

    for scenario in scenarios:

        # ボタンを大きく見せる
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
