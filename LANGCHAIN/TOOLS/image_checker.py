from image_fetcher import search_subchapter_by_query, fetch_figures_only

def check_images_for_query(query_name):
    subchapter = search_subchapter_by_query(query_name, top_k=1)

    if subchapter:
        figures = fetch_figures_only(subchapter)
        if figures:
            print(f"Images for '{subchapter}':")
            for fig in figures:
                print(f"  Name: {fig['name']}")
                print(f"  Path: {fig['path']}")
                print(f"  Description: {fig['desc']}")
        else:
            print(f"No images found for subchapter: '{subchapter}'.")
    else:
        print(f"No relevant subchapter found for: '{query_name}'.")

if __name__ == "__main__":
    check_images_for_query("Human brain")