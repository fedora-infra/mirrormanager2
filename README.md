# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/fedora-infra/mirrormanager2/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                                               |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|----------------------------------------------------------------------------------- | -------: | -------: | -------: | -------: | ------: | --------: |
| mirrormanager2/\_\_init\_\_.py                                                     |        2 |        0 |        0 |        0 |    100% |           |
| mirrormanager2/admin.py                                                            |       22 |        3 |        6 |        2 |     82% |39-\>41, 88-90 |
| mirrormanager2/api.py                                                              |       40 |       30 |       12 |        0 |     19% |66-93, 134-153 |
| mirrormanager2/app.py                                                              |       55 |        2 |        8 |        2 |     90% |85-\>89, 99-100 |
| mirrormanager2/auth.py                                                             |       35 |        5 |       16 |        4 |     75% |37-\>46, 50-51, 57, 93-94 |
| mirrormanager2/crawler/\_\_init\_\_.py                                             |        0 |        0 |        0 |        0 |    100% |           |
| mirrormanager2/crawler/cli.py                                                      |      155 |      155 |       36 |        0 |      0% |     1-341 |
| mirrormanager2/crawler/connection\_pool.py                                         |       52 |       14 |       14 |        2 |     73% |21, 41-\>55, 44-46, 58-63, 66, 69-71 |
| mirrormanager2/crawler/connector.py                                                |       71 |       30 |        8 |        0 |     52% |29-30, 38-39, 56-58, 61-64, 92-93, 97-113, 116-117, 128-130 |
| mirrormanager2/crawler/constants.py                                                |        8 |        0 |        0 |        0 |    100% |           |
| mirrormanager2/crawler/continents.py                                               |       53 |       35 |       12 |        0 |     28% |20, 28-35, 40-49, 53-84 |
| mirrormanager2/crawler/crawler.py                                                  |      362 |      302 |      118 |        0 |     12% |58-61, 64-65, 89-104, 109-116, 138-151, 161-201, 215-235, 238-277, 280-333, 336-374, 377-402, 405-448, 451-456, 460-474, 477-492, 496-560, 564-565, 573-602 |
| mirrormanager2/crawler/ftp\_connector.py                                           |       94 |       65 |       32 |        2 |     28% |17-20, 23-24, 27-40, 43-99, 102, 107-108, 113, 125 |
| mirrormanager2/crawler/http\_connector.py                                          |      100 |       38 |       32 |        4 |     61% |19, 55-61, 64, 97-116, 124-143, 148-150, 160-161, 174-175, 185 |
| mirrormanager2/crawler/log.py                                                      |       52 |       36 |        8 |        0 |     27% |23-29, 41, 44-47, 51-63, 68-88 |
| mirrormanager2/crawler/notif.py                                                    |       17 |        0 |        2 |        0 |    100% |           |
| mirrormanager2/crawler/reporter.py                                                 |       97 |       56 |       26 |        5 |     39% |15, 30-65, 72-79, 82-90, 101-104, 130-138, 141-142, 147-148, 150-\>158 |
| mirrormanager2/crawler/rsync\_connector.py                                         |       84 |       23 |       20 |        8 |     70% |20-22, 25-\>27, 30-32, 37-42, 43-\>46, 52-61, 72, 76-78, 87, 103-106, 129 |
| mirrormanager2/crawler/states.py                                                   |       21 |        0 |        0 |        0 |    100% |           |
| mirrormanager2/crawler/threads.py                                                  |       63 |       38 |       14 |        0 |     32% |33, 37-38, 42-43, 49-73, 78-80, 83, 87-98, 101 |
| mirrormanager2/crawler/ui.py                                                       |       96 |       72 |       28 |        1 |     20% |14, 18, 22-30, 35-41, 45-53, 56-57, 60-62, 65-66, 69, 72-75, 78-80, 83-84, 88-125, 131-142 |
| mirrormanager2/crawler/utils.py                                                    |        8 |        0 |        0 |        0 |    100% |           |
| mirrormanager2/database.py                                                         |        3 |        0 |        0 |        0 |    100% |           |
| mirrormanager2/default\_config.py                                                  |       46 |        0 |        0 |        0 |    100% |           |
| mirrormanager2/forms.py                                                            |       79 |        7 |        4 |        2 |     89% |41-42, 60-61, 154-156, 161, 214-\>exit |
| mirrormanager2/health\_checks.py                                                   |       14 |        3 |        4 |        0 |     83% |  8, 14-15 |
| mirrormanager2/lib/\_\_init\_\_.py                                                 |      382 |      129 |      136 |        5 |     65% |100-102, 133-135, 471, 478, 622, 633, 743, 759-765, 769-782, 802-812, 821-824, 833-835, 860-865, 876-884, 889-1000, 1012-1029, 1038-1056, 1066-1071, 1082-1087, 1096, 1105, 1116-1130, 1136-1142 |
| mirrormanager2/lib/constants.py                                                    |        3 |        0 |        0 |        0 |    100% |           |
| mirrormanager2/lib/database.py                                                     |        6 |        0 |        0 |        0 |    100% |           |
| mirrormanager2/lib/fedora.py                                                       |       21 |       16 |        2 |        0 |     22% | 19-39, 43 |
| mirrormanager2/lib/geo.py                                                          |       56 |       43 |       20 |        0 |     17% |16, 21-34, 39-67, 72-102 |
| mirrormanager2/lib/hostconfig.py                                                   |       68 |       34 |       46 |        8 |     47% |34-36, 38-39, 47-48, 53-54, 59-60, 65-66, 72-75, 96-123 |
| mirrormanager2/lib/migrations/env.py                                               |       37 |       13 |        6 |        1 |     58% |22-26, 45-48, 63-67, 87 |
| mirrormanager2/lib/migrations/versions/8d2832628792\_access\_statistics.py         |       16 |        8 |        0 |        0 |     50% |20-44, 48-51 |
| mirrormanager2/lib/migrations/versions/920e847c8c36\_add\_admin\_only\_category.py |        8 |        2 |        0 |        0 |     75% |    18, 22 |
| mirrormanager2/lib/migrations/versions/3264c6353b51\_indexes.py                    |       41 |       17 |        0 |        0 |     59% |     19-41 |
| mirrormanager2/lib/migrations/versions/24681dabe5fa\_add\_host\_columns.py         |       18 |       12 |        0 |        0 |     33% |18-23, 27-32 |
| mirrormanager2/lib/migrations/versions/b1f02d039900\_propagation\_statistics.py    |       14 |        6 |        0 |        0 |     57% |20-39, 48-50 |
| mirrormanager2/lib/migrations/versions/e67aacbf9f4f\_host\_geo\_coordinates.py     |       12 |        4 |        0 |        0 |     67% |20-21, 25-26 |
| mirrormanager2/lib/model.py                                                        |      524 |       25 |       40 |        1 |     93% |287-288, 379-388, 599, 780-806, 832 |
| mirrormanager2/lib/notifications.py                                                |       11 |        0 |        0 |        0 |    100% |           |
| mirrormanager2/lib/pid.py                                                          |       30 |       30 |        6 |        0 |      0% |     24-66 |
| mirrormanager2/lib/repomap.py                                                      |      273 |      220 |      234 |        8 |     14% |13-28, 37, 48-\>50, 70-\>72, 77-103, 108-122, 125-130, 139-377 |
| mirrormanager2/lib/sync.py                                                         |       39 |        4 |       14 |        1 |     87% |     51-55 |
| mirrormanager2/lib/umdl.py                                                         |      269 |       64 |      104 |       24 |     72% |60, 67-69, 75-80, 130, 132, 135-140, 150-151, 232-\>211, 241-242, 245, 248-256, 283-\>301, 286, 293-\>301, 308-\>314, 318, 327-\>329, 338-339, 346-347, 353-354, 357-373, 400-402, 410-411, 415-416, 421-422, 427-429, 440, 442-445, 469 |
| mirrormanager2/local\_auth.py                                                      |      172 |      147 |       36 |        0 |     12% |42-81, 90-140, 146-165, 173-205, 214-244, 261-281, 294-315, 326-329, 334-368, 373-382 |
| mirrormanager2/login\_forms.py                                                     |       23 |        4 |        2 |        0 |     76% |39-40, 45-46 |
| mirrormanager2/perms.py                                                            |       40 |        5 |       18 |        6 |     81% |9, 12-\>16, 14, 19, 24, 30 |
| mirrormanager2/utility/\_\_init\_\_.py                                             |        0 |        0 |        0 |        0 |    100% |           |
| mirrormanager2/utility/add\_product.py                                             |       58 |       58 |        6 |        0 |      0% |     5-125 |
| mirrormanager2/utility/common.py                                                   |       28 |        4 |       10 |        3 |     82% |26, 28, 38-39 |
| mirrormanager2/utility/create\_install\_repo.py                                    |       61 |       61 |       10 |        0 |      0% |     5-120 |
| mirrormanager2/utility/emergency\_expire\_repo.py                                  |       42 |       42 |       10 |        0 |      0% |     33-95 |
| mirrormanager2/utility/expire\_statistics.py                                       |       20 |       20 |        0 |        0 |      0% |      7-40 |
| mirrormanager2/utility/generate\_worldmap.py                                       |       39 |       39 |       12 |        0 |      0% |     10-58 |
| mirrormanager2/utility/last\_sync.py                                               |       49 |       49 |       16 |        0 |      0% |    22-147 |
| mirrormanager2/utility/mirrorlist\_statistics.py                                   |       73 |       73 |       10 |        0 |      0% |    24-131 |
| mirrormanager2/utility/move\_devel\_to\_release.py                                 |       56 |        6 |       20 |        6 |     84% |84, 86-\>74, 90-91, 96, 104, 126 |
| mirrormanager2/utility/move\_to\_archive.py                                        |       75 |        8 |       38 |        7 |     87% |44-45, 47-48, 50-54, 68-\>66, 71-\>exit, 136, 143 |
| mirrormanager2/utility/netblocks.py                                                |      189 |       84 |       52 |        3 |     52% |66-82, 86-90, 94, 99-110, 121-146, 156-166, 174-175, 187-189, 194-198, 202-217, 228, 269, 276-278, 337-340 |
| mirrormanager2/utility/pagination.py                                               |       63 |       16 |       14 |        4 |     69% |21-22, 40, 44, 53-59, 64, 66, 72, 79, 82-84 |
| mirrormanager2/utility/update\_ec2\_netblocks.py                                   |       67 |       67 |       30 |        0 |      0% |     6-107 |
| mirrormanager2/utility/update\_master\_directory\_list.py                          |      461 |      224 |      162 |       27 |     48% |68, 73-78, 92, 94, 96-107, 136-137, 140-141, 147-156, 160-\>166, 172-\>175, 178, 179-\>181, 184, 203-\>206, 207, 210-\>214, 220-\>227, 230-\>233, 241-242, 252-253, 257-270, 273-274, 277-324, 327-343, 346-362, 368-369, 383-386, 392-394, 406, 421, 433-\>378, 437-438, 459-461, 464-491, 512-521, 529-530, 537-600, 610-675, 684-689, 748-752, 786-791, 792-\>799, 794-\>796, 799-\>exit, 812 |
| mirrormanager2/utility/update\_single\_file\_detail.py                             |       36 |        3 |        8 |        2 |     89% | 58-59, 65 |
| mirrormanager2/utility/upgrade\_install\_repo.py                                   |       62 |       62 |       20 |        0 |      0% |    14-131 |
| mirrormanager2/views.py                                                            |      684 |      188 |      236 |       25 |     71% |76-\>82, 84-\>88, 163, 219-\>223, 253-289, 302, 325-346, 361-406, 419, 464, 516-\>520, 536-557, 572-601, 623, 663, 709, 747, 794, 833, 892, 931, 944-\>948, 949, 992, 1036, 1060-\>1062, 1069-\>1072, 1077-1081, 1112, 1156-1209, 1218-1243, 1263, 1269, 1274-1275, 1286-1313, 1320-1342, 1349-1350 |
| mirrormanager2/xml\_rpc.py                                                         |       36 |        2 |        2 |        1 |     92% |     79-80 |
| **TOTAL**                                                                          | **5791** | **2703** | **1720** |  **164** | **49%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/fedora-infra/mirrormanager2/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/fedora-infra/mirrormanager2/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/fedora-infra/mirrormanager2/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/fedora-infra/mirrormanager2/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Ffedora-infra%2Fmirrormanager2%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/fedora-infra/mirrormanager2/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.