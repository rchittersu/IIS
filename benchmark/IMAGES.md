# Insert In Style Bench: per-image sources

Generated from [`image_sources.csv`](image_sources.csv), which is what [`retrieve_images.py`](retrieve_images.py) reads. **Ships** = included in `benchmark/` (our own images); every other image is fetched from its source.

**Crop** is `x0 y0 x1 y1` in the source image (after EXIF rotation); the crop is then resized to **Size**. **Check** is how the rebuilt file is verified: `md5` for files used as-is, `dhash` for cropped or resized ones.

## Backgrounds

| # | File | Source | Page | Path in source | Crop | Size | Check | Licence | Pairs |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `set1/cartoon/000000000662.jpg` | Human-Art | [IDEA-Research/HumanArt](https://github.com/IDEA-Research/HumanArt) | `images/2D_virtual_human/cartoon/000000000662.jpg` | — | 517x800 | md5 | Human-Art terms (access on request) | 15 |
| 2 | `set1/cartoon/000000003103.jpg` | Human-Art | [IDEA-Research/HumanArt](https://github.com/IDEA-Research/HumanArt) | `images/2D_virtual_human/cartoon/000000003103.jpg` | — | 1080x607 | md5 | Human-Art terms (access on request) | 16 |
| 3 | `set1/cartoon/000000004761.jpg` | Human-Art | [IDEA-Research/HumanArt](https://github.com/IDEA-Research/HumanArt) | `images/2D_virtual_human/cartoon/000000004761.jpg` | — | 1080x583 | md5 | Human-Art terms (access on request) | 19 |
| 4 | `set1/digital/000000000004.jpg` | Human-Art | [IDEA-Research/HumanArt](https://github.com/IDEA-Research/HumanArt) | `images/2D_virtual_human/digital_art/000000000004.jpg` | — | 1280x1611 | md5 | Human-Art terms (access on request) | 9 |
| 5 | `set1/digital/000000000345.jpg` | Human-Art | [IDEA-Research/HumanArt](https://github.com/IDEA-Research/HumanArt) | `images/2D_virtual_human/digital_art/000000000345.jpg` | — | 1024x1211 | md5 | Human-Art terms (access on request) | 20 |
| 6 | `set1/digital/000000000475.jpg` | Human-Art | [IDEA-Research/HumanArt](https://github.com/IDEA-Research/HumanArt) | `images/2D_virtual_human/digital_art/000000000475.jpg` | — | 1600x2106 | md5 | Human-Art terms (access on request) | 18 |
| 7 | `set1/digital/000000000586.jpg` | Human-Art | [IDEA-Research/HumanArt](https://github.com/IDEA-Research/HumanArt) | `images/2D_virtual_human/digital_art/000000000586.jpg` | — | 1280x1883 | md5 | Human-Art terms (access on request) | 21 |
| 8 | `set1/digital/000000000769.jpg` | Human-Art | [IDEA-Research/HumanArt](https://github.com/IDEA-Research/HumanArt) | `images/2D_virtual_human/digital_art/000000000769.jpg` | — | 842x1191 | md5 | Human-Art terms (access on request) | 19 |
| 9 | `set1/digital/000000000770.jpg` | Human-Art | [IDEA-Research/HumanArt](https://github.com/IDEA-Research/HumanArt) | `images/2D_virtual_human/digital_art/000000000770.jpg` | — | 1169x1654 | md5 | Human-Art terms (access on request) | 6 |
| 10 | `set1/digital/000000000776.jpg` | Human-Art | [IDEA-Research/HumanArt](https://github.com/IDEA-Research/HumanArt) | `images/2D_virtual_human/digital_art/000000000776.jpg` | — | 877x1240 | md5 | Human-Art terms (access on request) | 19 |
| 11 | `set1/digital/000000000778.jpg` | Human-Art | [IDEA-Research/HumanArt](https://github.com/IDEA-Research/HumanArt) | `images/2D_virtual_human/digital_art/000000000778.jpg` | — | 877x1240 | md5 | Human-Art terms (access on request) | 16 |
| 12 | `set1/digital/000000001012.jpg` | Human-Art | [IDEA-Research/HumanArt](https://github.com/IDEA-Research/HumanArt) | `images/2D_virtual_human/digital_art/000000001012.jpg` | — | 800x1067 | md5 | Human-Art terms (access on request) | 18 |
| 13 | `set1/digital/000000001032.jpg` | Human-Art | [IDEA-Research/HumanArt](https://github.com/IDEA-Research/HumanArt) | `images/2D_virtual_human/digital_art/000000001032.jpg` | — | 4096x4096 | md5 | Human-Art terms (access on request) | 13 |
| 14 | `set1/digital/000000001277.jpg` | Human-Art | [IDEA-Research/HumanArt](https://github.com/IDEA-Research/HumanArt) | `images/2D_virtual_human/digital_art/000000001277.jpg` | — | 1024x1597 | md5 | Human-Art terms (access on request) | 15 |
| 15 | `set1/digital/000000001563.jpg` | Human-Art | [IDEA-Research/HumanArt](https://github.com/IDEA-Research/HumanArt) | `images/2D_virtual_human/digital_art/000000001563.jpg` | — | 682x1000 | md5 | Human-Art terms (access on request) | 13 |
| 16 | `set1/digital/000000001932.jpg` | Human-Art | [IDEA-Research/HumanArt](https://github.com/IDEA-Research/HumanArt) | `images/2D_virtual_human/digital_art/000000001932.jpg` | — | 3699x4500 | md5 | Human-Art terms (access on request) | 17 |
| 17 | `set1/digital/000000001988.jpg` | Human-Art | [IDEA-Research/HumanArt](https://github.com/IDEA-Research/HumanArt) | `images/2D_virtual_human/digital_art/000000001988.jpg` | — | 1024x768 | md5 | Human-Art terms (access on request) | 16 |
| 18 | `set1/digital/000000002933.jpg` | Human-Art | [IDEA-Research/HumanArt](https://github.com/IDEA-Research/HumanArt) | `images/2D_virtual_human/digital_art/000000002933.jpg` | — | 825x896 | md5 | Human-Art terms (access on request) | 16 |
| 19 | `set1/digital/000000003124.jpg` | Human-Art | [IDEA-Research/HumanArt](https://github.com/IDEA-Research/HumanArt) | `images/2D_virtual_human/digital_art/000000003124.jpg` | — | 1280x1280 | md5 | Human-Art terms (access on request) | 8 |
| 20 | `set2/images/WEB_003.jpg` | Web image (not distributed) | — | — | — | 3000x3000 | — | — | 17 |
| 21 | `set2/images/WEB_004.jpg` | Kaggle devanshagarwal9/artistic-styles | [devanshagarwal9/artistic-styles](https://www.kaggle.com/datasets/devanshagarwal9/artistic-styles) | `surrealism/00ceec475cb65a56223c14a2394ed4e8.jpg` | 263 0 793 530 | 530x530 | dhash | Unknown (not stated on Kaggle) | 20 |
| 22 | `set2/images/WEB_005.jpg` | Kaggle devanshagarwal9/artistic-styles | [devanshagarwal9/artistic-styles](https://www.kaggle.com/datasets/devanshagarwal9/artistic-styles) | `digital_scenery/0d5ccde52c4f7f578b29da3f7b39f5bc.jpg` | 0 70 1280 1350 | 1280x1280 | dhash | Unknown (not stated on Kaggle) | 19 |
| 23 | `set2/images/WEB_006.jpg` | Kaggle devanshagarwal9/artistic-styles | [devanshagarwal9/artistic-styles](https://www.kaggle.com/datasets/devanshagarwal9/artistic-styles) | `cartoon/3bb5e795c84612f413f41cead8187005.jpg` | 0 287 1080 1367 | 1080x1080 | dhash | Unknown (not stated on Kaggle) | 20 |
| 24 | `set2/images/WEB_007.jpg` | Kaggle devanshagarwal9/artistic-styles | [devanshagarwal9/artistic-styles](https://www.kaggle.com/datasets/devanshagarwal9/artistic-styles) | `cyberpunk/04a1ee6e87a1461f6c410659feec3497.jpg` | 277 0 1012 735 | 735x735 | dhash | Unknown (not stated on Kaggle) | 21 |
| 25 | `set2/images/WEB_008.png` | Kaggle unidpro/artistic-styles-dataset | [unidpro/artistic-styles-dataset](https://www.kaggle.com/datasets/unidpro/artistic-styles-dataset) | `images/008_00028.png` | — | 600x600 | md5 | CC BY-NC-ND 4.0 | 12 |
| 26 | `set2/images/WEB_010.png` | Kaggle unidpro/artistic-styles-dataset | [unidpro/artistic-styles-dataset](https://www.kaggle.com/datasets/unidpro/artistic-styles-dataset) | `images/023_00735.png` | 23 0 463 440 | 440x440 | dhash | CC BY-NC-ND 4.0 | 10 |
| 27 | `set2/images/WEB_011.jpg` | Kaggle devanshagarwal9/artistic-styles | [devanshagarwal9/artistic-styles](https://www.kaggle.com/datasets/devanshagarwal9/artistic-styles) | `anime/25c7efa8bfe8db44a79ff630d11cb479.jpg` | 0 97 736 833 | 736x736 | dhash | Unknown (not stated on Kaggle) | 16 |
| 28 | `set2/images/WEB_018.png` | **Ships** | — | — | — | 1024x1024 | — | ours | 18 |
| 29 | `set2/images/WEB_019.png` | **Ships** | — | — | — | 1024x1024 | — | ours | 18 |
| 30 | `set2/images/WEB_022.jpg` | Kaggle bodhisattamaiti/stylecruxgen | [bodhisattamaiti/stylecruxgen](https://www.kaggle.com/datasets/bodhisattamaiti/stylecruxgen) | `StyleCruxGen_1024_v2/09_v1_charcoaldrawing_mid_g5.jpg` | — | 1024x1024 | md5 | CC BY-NC-SA 4.0 | 14 |
| 31 | `set2/images/WEB_023.jpg` | Kaggle bodhisattamaiti/stylecruxgen | [bodhisattamaiti/stylecruxgen](https://www.kaggle.com/datasets/bodhisattamaiti/stylecruxgen) | `StyleCruxGen_1024_v2/12_v3_glasspainting_prepend_g8.jpg` | — | 1024x1024 | md5 | CC BY-NC-SA 4.0 | 11 |
| 32 | `set2/images/WEB_027.jpg` | Kaggle bodhisattamaiti/stylecruxgen | [bodhisattamaiti/stylecruxgen](https://www.kaggle.com/datasets/bodhisattamaiti/stylecruxgen) | `StyleCruxGen_1024_v3/19_v1_neonglow_prepend_g11.jpg` | — | 1024x1024 | md5 | CC BY-NC-SA 4.0 | 17 |
| 33 | `set2/images/WEB_028.jpg` | Kaggle shubham1921/real-to-ghibli-image-dataset-5k-paired-images | [shubham1921/real-to-ghibli-image-dataset-5k-paired-images](https://www.kaggle.com/datasets/shubham1921/real-to-ghibli-image-dataset-5k-paired-images) | `dataset/trainB_ghibli/studio_2307.jpg` | 412 0 1450 1038 | 1038x1038 | dhash | CC BY-NC 4.0 | 14 |
| 34 | `set2/images/WEB_029.jpg` | Kaggle shubham1921/real-to-ghibli-image-dataset-5k-paired-images | [shubham1921/real-to-ghibli-image-dataset-5k-paired-images](https://www.kaggle.com/datasets/shubham1921/real-to-ghibli-image-dataset-5k-paired-images) | `dataset/trainB_ghibli/studio_2388.jpg` | 702 0 1740 1038 | 1038x1038 | dhash | CC BY-NC 4.0 | 9 |
| 35 | `set3/images/image_1898.jpeg` | WikiArt | [pyotr-konchalovsky/still-life-white-partridge-1953](https://www.wikiart.org/en/pyotr-konchalovsky/still-life-white-partridge-1953) | — | 56 2 706 652 | 1382x1382 | dhash | see the WikiArt page; some works are still in copyright | 8 |
| 36 | `set3/images/image_1908.jpeg` | WikiArt | [vincent-van-gogh/vase-with-flowers-coffeepot-and-fruit-1887](https://www.wikiart.org/en/vincent-van-gogh/vase-with-flowers-coffeepot-and-fruit-1887) | — | 0 47 1764 1811 | 1382x1382 | dhash | see the WikiArt page; some works are still in copyright | 18 |
| 37 | `set3/images/image_1941.jpeg` | WikiArt | [boris-kustodiev/easter-greeting-1916](https://www.wikiart.org/en/boris-kustodiev/easter-greeting-1916) | — | 2 1 824 823 | 1382x1382 | dhash | see the WikiArt page; some works are still in copyright | 11 |
| 38 | `set3/images/image_2001.jpeg` | WikiArt | [pierre-auguste-renoir/still-life-with-melon-1882](https://www.wikiart.org/en/pierre-auguste-renoir/still-life-with-melon-1882) | — | 15 1 883 869 | 1382x1382 | dhash | see the WikiArt page; some works are still in copyright | 18 |
| 39 | `set3/images/image_2037.jpeg` | WikiArt | [paul-cezanne/still-life-flowers-in-a-vase-1888](https://www.wikiart.org/en/paul-cezanne/still-life-flowers-in-a-vase-1888) | — | 443 0 2536 2093 | 1382x1382 | dhash | see the WikiArt page; some works are still in copyright | 18 |
| 40 | `set3/images/image_2132.jpeg` | WikiArt | [pierre-auguste-renoir/still-life-a-plate-of-plums](https://www.wikiart.org/en/pierre-auguste-renoir/still-life-a-plate-of-plums) | — | 2 2 660 660 | 1382x1382 | dhash | see the WikiArt page; some works are still in copyright | 19 |
| 41 | `set3/images/image_312.jpeg` | WikiArt | [pyotr-konchalovsky/still-life-bread-ham-and-wine-1948](https://www.wikiart.org/en/pyotr-konchalovsky/still-life-bread-ham-and-wine-1948) | — | 22 0 605 583 | 1382x1382 | dhash | see the WikiArt page; some works are still in copyright | 7 |
| 42 | `set3/images/image_39100.jpeg` | WikiArt | [charles-cottet/the-child-death-1897](https://www.wikiart.org/en/charles-cottet/the-child-death-1897) | — | 0 48 404 452 | 1382x1382 | dhash | see the WikiArt page; some works are still in copyright | 20 |
| 43 | `set3/images/image_39315.jpeg` | WikiArt | [balthus/still-life-with-a-figure-1942](https://www.wikiart.org/en/balthus/still-life-with-a-figure-1942) | — | 102 5 1287 1190 | 1382x1382 | dhash | see the WikiArt page; some works are still in copyright | 15 |
| 44 | `set3/images/image_39407.jpeg` | WikiArt | [adriaen-van-ostade/the-call](https://www.wikiart.org/en/adriaen-van-ostade/the-call) | — | 0 103 1165 1268 | 1381x1381 | dhash | see the WikiArt page; some works are still in copyright | 19 |
| 45 | `set3/images/image_39458.jpeg` | WikiArt | [paul-gauguin/at-the-window-1882](https://www.wikiart.org/en/paul-gauguin/at-the-window-1882) | — | 116 1 711 596 | 1382x1382 | dhash | see the WikiArt page; some works are still in copyright | 17 |
| 46 | `set3/images/image_39492.jpeg` | WikiArt | [edouard-vuillard/vase-of-flowers-1903](https://www.wikiart.org/en/edouard-vuillard/vase-of-flowers-1903) | — | 0 100 812 912 | 1382x1382 | dhash | see the WikiArt page; some works are still in copyright | 16 |
| 47 | `set3/images/image_39574.jpeg` | WikiArt | [jacek-malczewski/christmas-eve-in-siberia-1892](https://www.wikiart.org/en/jacek-malczewski/christmas-eve-in-siberia-1892) | — | 404 0 1024 620 | 1382x1382 | dhash | see the WikiArt page; some works are still in copyright | 19 |
| 48 | `set3/images/image_39749.jpeg` | WikiArt | [adriaen-van-ostade/smiling-smoker](https://www.wikiart.org/en/adriaen-van-ostade/smiling-smoker) | — | 0 33 454 487 | 1382x1382 | dhash | see the WikiArt page; some works are still in copyright | 12 |
| 49 | `set3/images/image_39757.jpeg` | WikiArt | [gerard-terborch/the-violinist](https://www.wikiart.org/en/gerard-terborch/the-violinist) | — | 1 243 1013 1255 | 1382x1382 | dhash | see the WikiArt page; some works are still in copyright | 11 |
| 50 | `set3/images/image_39916.jpeg` | WikiArt | [maurice-de-vlaminck/still-life](https://www.wikiart.org/en/maurice-de-vlaminck/still-life) | — | 142 0 758 616 | 1382x1382 | dhash | see the WikiArt page; some works are still in copyright | 13 |
| 51 | `set3/images/image_40059.jpeg` | WikiArt | [ilya-mashkov/fruits-1938](https://www.wikiart.org/en/ilya-mashkov/fruits-1938) | — | 98 0 873 775 | 1382x1382 | dhash | see the WikiArt page; some works are still in copyright | 17 |

## Foregrounds

| # | File | Source | Page | Path in source | Crop | Size | Check | Licence | Pairs |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `selected_subjects/apple.png` | **Ships** | — | — | — | 1024x1024 | — | ours | 41 |
| 2 | `selected_subjects/backpack.png` | **Ships** | — | — | — | 1024x1024 | — | ours | 43 |
| 3 | `selected_subjects/berry_bowl.png` | DreamBooth | [google/dreambooth](https://github.com/google/dreambooth) | `dataset/berry_bowl/02.jpg` | 92 207 1107 1073 | 1015x866 | dhash | DreamBooth authors' photo; free to modify and distribute | 40 |
| 4 | `selected_subjects/book.png` | **Ships** | — | — | — | 1024x1024 | — | ours | 2 |
| 5 | `selected_subjects/burger.png` | **Ships** | — | — | — | 1024x1024 | — | ours | 47 |
| 6 | `selected_subjects/camera.png` | **Ships** | — | — | — | 1024x1024 | — | ours | 19 |
| 7 | `selected_subjects/can.png` | DreamBooth | [google/dreambooth](https://github.com/google/dreambooth) | `dataset/can/00.jpg` | 408 193 878 1038 | 470x845 | dhash | DreamBooth authors' photo; free to modify and distribute | 10 |
| 8 | `selected_subjects/candle.png` | DreamBooth | [google/dreambooth](https://github.com/google/dreambooth) | `dataset/candle/04.jpg` | 713 816 1416 1514 | 444x441 | dhash | DreamBooth authors' photo; free to modify and distribute | 4 |
| 9 | `selected_subjects/cat.png` | DreamBooth | [google/dreambooth](https://github.com/google/dreambooth) | `dataset/cat/03.jpg` | 412 105 1029 1245 | 617x1140 | dhash | DreamBooth authors' photo; free to modify and distribute | 35 |
| 10 | `selected_subjects/clock.png` | DreamBooth | [google/dreambooth](https://github.com/google/dreambooth) | `dataset/clock/04.jpg` | 277 140 1061 1249 | 747x1057 | dhash | DreamBooth authors' photo; free to modify and distribute | 27 |
| 11 | `selected_subjects/dog.png` | **Ships** | — | — | — | 1024x1024 | — | ours | 43 |
| 12 | `selected_subjects/duck_toy.png` | **Ships** | — | — | — | 1024x1024 | — | ours | 47 |
| 13 | `selected_subjects/german_shephard_dog.png` | **Ships** | — | — | — | 1024x1024 | — | ours | 16 |
| 14 | `selected_subjects/grey_sloth_plushie.png` | DreamBooth | [google/dreambooth](https://github.com/google/dreambooth) | `dataset/grey_sloth_plushie/01.jpg` | 321 552 1757 1922 | 908x866 | dhash | DreamBooth authors' photo; free to modify and distribute | 29 |
| 15 | `selected_subjects/kite.png` | **Ships** | — | — | — | 1024x1024 | — | ours | 29 |
| 16 | `selected_subjects/monster_toy.png` | DreamBooth | [google/dreambooth](https://github.com/google/dreambooth) | `dataset/monster_toy/01.jpg` | 377 115 1305 1230 | 835x1003 | dhash | DreamBooth authors' photo; free to modify and distribute | 10 |
| 17 | `selected_subjects/mug.png` | **Ships** | — | — | — | 1024x1024 | — | ours | 43 |
| 18 | `selected_subjects/rat.png` | **Ships** | — | — | — | 1024x1024 | — | ours | 44 |
| 19 | `selected_subjects/rc_car.png` | DreamBooth | [google/dreambooth](https://github.com/google/dreambooth) | `dataset/rc_car/03.jpg` | 280 135 1071 1343 | 710x1084 | dhash | DreamBooth authors' photo; free to modify and distribute | 1 |
| 20 | `selected_subjects/robot_toy.png` | **Ships** | — | — | — | 1024x1024 | — | ours | 39 |
| 21 | `selected_subjects/straw_hat.png` | **Ships** | — | — | — | 1024x1024 | — | ours | 36 |
| 22 | `selected_subjects/teapot.png` | **Ships** | — | — | — | 1024x1024 | — | ours | 48 |
| 23 | `selected_subjects/teddy_bear.png` | **Ships** | — | — | — | 1024x1024 | — | ours | 50 |
| 24 | `selected_subjects/vase.png` | **Ships** | — | — | — | 1024x1024 | — | ours | 41 |
| 25 | `selected_subjects/wolf_plushie.png` | DreamBooth | [google/dreambooth](https://github.com/google/dreambooth) | `dataset/wolf_plushie/00.jpg` | 222 519 1507 1531 | 815x642 | dhash | DreamBooth authors' photo; free to modify and distribute | 44 |
