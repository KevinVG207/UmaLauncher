from mdb_conn import Connection
import requests
import time
import os
from multiprocessing import Pool

URL_PREFIX = "https://raw.githubusercontent.com/KevinVG207/umamusu-translate/mdb-update/translations/mdb/"
INDEX_URL = "https://raw.githubusercontent.com/KevinVG207/umamusu-translate/mdb-update/src/mdb/index.json"

def fetch_json(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def make_tl_url(filename):
    return URL_PREFIX + filename + ".json"

def get_table(table, columns, dest):
    with Connection() as (_, cursor):
        cursor.execute(
            f"""SELECT {columns}, {dest} FROM {table}"""
        )
        rows = cursor.fetchall()
    
    if not rows:
        return {}
    
    data_dict = {}

    def add_to_dict(parent_dict, values_list):
        if len(values_list) == 2:
            parent_dict[values_list[0]] = values_list[1]
        else:
            if values_list[0] not in parent_dict:
                parent_dict[values_list[0]] = {}
            add_to_dict(parent_dict[values_list[0]], values_list[1:])
    
    for row in rows:
        add_to_dict(data_dict, row)
    
    return data_dict

def make_category(id, sql=None, tlg=None):
    return {
        "id": id,
        "sql": sql,
        "tlg": tlg
    }

def patch_table(table, pre_patch, columns, dest):
    print("Writing table: " + table)
    with Connection() as (conn, cursor):
        i = 0
        for cat, index_data in pre_patch.items():
            # print(f"Writing category {cat}")
            for index, text in index_data.items():
                i += 1
                if i % 1000 == 0:
                    # print(f"Writing row {i}")
                    pass
                cursor.execute(
                    f"""UPDATE {table} SET {dest} = ? WHERE {columns[0]} = ? AND {columns[1]} = ?""",
                    (text, cat, index)
                )
        conn.commit()
    print(f"{i} rows written")

def patch_mdb():
    index = fetch_json(INDEX_URL)

    for table in index:
        if table["table"] != 'text_data':
            continue  # TODO: Implement other tables

        print("Patching table: " + table["table"])

        pre_patch = get_table(table['table'], "category, \"index\"", 'text')

        post_patch = {}

        pool_before = time.perf_counter()
        with Pool(processes=min(os.cpu_count(), 16)) as pool:
            result = pool.map(fetch_json, [make_tl_url(file) for file in table['files'].keys()])
            file_jsons = {file: json for file, json in zip(table['files'].keys(), result)}
        pool_after = time.perf_counter()
        print(f"Fetch time: {pool_after - pool_before}")

        process_before = time.perf_counter()
        for file, metadata in table['files'].items():
            # print("Patching file: " + file)
            file_json = file_jsons[file]
            replace_dict = {k: v for k, v in file_json['text'].items() if v}

            categories = []

            if not isinstance(metadata, dict):
                if not isinstance(metadata, list):
                    categories.append(make_category(metadata))
                else:
                    for category in metadata:
                        if isinstance(category, dict):
                            categories.append(make_category(category['spec'], category.get('sql', None), category.get('tlg', False)))
                        else:
                            categories.append(make_category(category))
            else:
                # Data is a dictionary
                category_ids = metadata.get('spec', [])
                sql = metadata.get('sql', None)
                tlg = metadata.get('tlg', False)

                if isinstance(category_ids, int):
                    category_ids = [category_ids]

                for category_id in category_ids:
                    categories.append(make_category(category_id, sql, tlg))


            if categories[0]['id'] == None:
                categories = [make_category(cat_id) for cat_id in pre_patch.keys()]

            for cat_data in categories:
                if cat_data['id'] not in post_patch:
                    post_patch[cat_data['id']] = {}

                category_rows = pre_patch[cat_data['id']]

                for index, text in category_rows.items():
                    if text in replace_dict:
                        post_patch[cat_data['id']][index] = replace_dict[text]
        
        process_after = time.perf_counter()
        print(f"Process time: {process_after - process_before}")
        
        write_before = time.perf_counter()
        patch_table(table['table'], post_patch, ['category', '"index"'], 'text')
        write_after = time.perf_counter()
        print(f"Write time: {write_after - write_before}")

def main():
    tot_before = time.perf_counter()
    patch_mdb()
    tot_after = time.perf_counter()
    print(f"Total time: {tot_after - tot_before}")

if __name__ == "__main__":
    main()