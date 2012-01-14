<div xmlns:py="http://purl.org/kid/ns#">
<button class="blue_button" onclick="cat_browse.adding('${object_name}')" accesskey="+">Add ${object_name} <span style="font-size:14px">+</span></button>
  <table style="margin-top:4px" id="${object_name}" class="grid" cellpadding="0" cellspacing="1" border="0">
    <?python
       gt = lambda a,b: a > b
       current_page = (start / (page_size or 1)) + 1
       page_size_options = [10,30,50,100,500,1000]
       if page_size not in page_size_options: page_size_options.append(page_size)
       page_size_options.sort()
       last_record = start + page_size
       if last_record > total: last_record = total
       paging_window = 20 
       half_window = paging_window / 2
       pages = total/(page_size or 1)
       if total % page_size: pages += 1
       pages = range(pages)
       if len(pages) > paging_window:
        if current_page > half_window:
            pages = pages[current_page - half_window : current_page + half_window] 
        else:
            pages = pages[:paging_window]

    ?>
    <tr>
        <td colspan="2" align="center" valign="bottom"></td> 
        <td align="center" colspan="${len(headers)}">
            <span style="float:left;margin-top:3px">
                Records 
                ${start} - ${last_record} 
                (total:${total})
            </span>
            <span style="float:right">
                Page size:
                <select name="page_size" 
                    onchange="cat_browse.update_page_size('${object_name}',this,'${start}')">

                    <option py:for="idx in page_size_options"
                        py:attrs="dict(value=idx,selected=(idx==page_size and 'selected' or None))">
                        ${idx}
                    </option>
                </select>
            </span>

            <span py:if="gt(total,len(rows))">
                <span py:if="gt(current_page,1)">
                    <a href="javascript:cat_browse.previous_page('${object_name}','${start}','${page_size}')" 
                        title="Previous"><img align="absbottom" class="page_arrow" 
                            src="${tg.tg_static}/images/arrow_left.png" border="0" /></a>  
                </span>

                <select 
                        class="page_select" name="page" 
                        onchange="cat_browse.update_page('${object_name}',this,'${page_size}')">
                    <option py:for="idx in pages"
                        py:attrs="dict(value=(idx * page_size),selected=((idx + 1)==current_page and 'selected' or None))">
                        ${idx + 1}
                    </option>
                </select>

                <span py:if="gt(pages[-1],(current_page-1))">
                    <a href="javascript:cat_browse.next_page('${object_name}','${start}','${page_size}')" 
                        title="Next"><img align="absbottom" class="page_arrow" 
                            src="${tg.tg_static}/images/arrow_right.png" border="0" /></a>
                </span>
            </span>

        </td>
    </tr>
    <tr>
        <td colspan="2"></td>
        <td colspan="${len(headers)}" style="padding:0"><img src="${tg.tg_static}/images/transp.png" height="1" width="650"/></td>
    </tr>
    <tr py:if="headers">
      <th colspan="2" 
        style="background-color:#e3e3e3;padding:0"><a title="Manage Columns" 
            onclick="cat_browse.manage_columns('${object_name}','${start}','${page_size}')"
            href="#"><img style="float:right;margin-right:3px" 
            src="${tg.tg_static}/images/table.gif" border="0" /></a>
      </th> 
      <th py:for="col in headers" valign="top">
        ${col['title'] or col['name'].capitalize()}
      </th>
    </tr>
    <tr py:for="i, row in enumerate(rows)" 
        id="${object_name}_row_${row['id']}"
        onmouseover="cat_browse.highlight(this,true)"
        onmouseout="cat_browse.highlight(this,false,'#${i%2 and 'edf3fe' or 'fff'}')"
        class="${i%2 and 'odd' or 'even'}">

      <td class="grid_icon_cell"><a href="#" 
        id="${object_name}_row_${row['id']}_delete"
        onclick="cat_browse.deleting('${object_name}','${row['id']}')"
        class="grid_icon" title="Delete Record"><img src="${tg.tg_static}/images/trash.png" border="0" /></a></td>
      <td class="grid_icon_cell"><a href="#" 
        onclick="cat_browse.editing('${object_name}','${row['id']}')"
        id="${object_name}_row_${row['id']}_edit"
        class="grid_icon" title="Edit Record"><img src="${tg.tg_static}/images/edit.png" border="0" /></a></td>
      <td valign="top" py:for="col in headers" onclick="cat_browse.selecting('${object_name}','${row['id']}');" >
        ${row.get(col['name'],'')}
      </td>
    </tr>
  </table>
</div>
