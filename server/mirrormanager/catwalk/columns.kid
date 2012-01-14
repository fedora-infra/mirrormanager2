<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" >
<head>
    <meta content="text/html; charset=UTF-8" http-equiv="content-type" />
    <script language="JavaScript" src="${tg.tg_static}/js/tool-man/core.js"></script>
    <script language="JavaScript" src="${tg.tg_static}/js/tool-man/events.js"></script>
    <script language="JavaScript" src="${tg.tg_static}/js/tool-man/css.js"></script>
    <script language="JavaScript" src="${tg.tg_static}/js/tool-man/coordinates.js"></script>
    <script language="JavaScript" src="${tg.tg_static}/js/tool-man/drag.js"></script>
    <script language="JavaScript" src="${tg.tg_static}/js/tool-man/dragsort.js"></script>
    <script language="JavaScript" src="${tg.tg_js}/MochiKit.js"></script>
    <style>
        #columns
        {
            list-style:none;
            margin:0;padding:0;
            font-size:12px;
            font-family:verdana,sans-serif;
        }
        li { margin-bottom:2px;padding-bottom:0px;border-bottom:1px solid #e3e3e3 }
        #columns a { color:#333;text-decoration:none}
        .handle {
        width: 10px;
        cursor:move;
        visibility:hidden;
        font-size:14px;
        font-weight:900;
        }
        .col_type {color:#c0c0c0;}
        .column_label { list-style:none; }
        .column_label li {border-bottom:1px solid #fff; }
         .column_menu
        {
            position:relative;
            display:none;
            margin:0;
            padding:0;
        }

        .column_menu li { padding:0;margin:0 }
        .column_menu a { background-color:#e3e3e3;padding:5px;display:block;width:100% }
        .column_menu a:hover { background-color:#cdcdcd }

        .blue_button
        {
            cursor:pointer;
            color:#fff;
            background-color:#1E75BC;
            border-width:0px;
            margin-left:0px;
            padding:3px;
            width:130px;
            text-align:center;
        }
    </style>
</head>
<body style="margin:20px;">
    <br />
    <form name="columns" action="save_columns" method="post">
        <input type="hidden" name="object_name" value="${object_name}" />
        <input type="hidden" name="context" value="${context}" />
        <input type="hidden" name="order" value="${'|'.join([x['name'] for x in columns])}" />
        <input type="hidden" name="hidden_columns" value="${'|'.join([x['name'] for x in columns if not x['visible']])}" />
        <input type="hidden" name="updated_fk_labels" value="" />
    <ul id="columns">
      <li py:for="col in columns"
        onmouseover="document.getElementById('handle_${col['name']}').style.visibility='visible'"
        onmouseout="document.getElementById('handle_${col['name']}').style.visibility='hidden'"
        id="${col['name']}">
        <table border="0">
          <tr>
            <td valign="top" id="handle_${col['name']}"
                title="Reorder the columns" class="handle">&#x2195;</td>
            <td valign="top">
                <a href="javascript:toggle_check('${col['name']}')"><img
                        id="img_${col['name']}"
                        width="15" height="15"
                        align="absbottom"
                        class="visibility_status"
                        title="Toggle the column visibility"
                        src="${tg.tg_static}/images/${('transp','save')[col['visible']]}.png"
                        border="0" />${col['title'] or col['name'].capitalize()}</a>
                <span py:if="col['title']" class="col_type">[${col['name']}]</span>
            </td>
            <td valign="top" class="col_type">
                ${col['type']}
                <span py:if="'other_class_name' in col">
                    : ${col['other_class_name']}
                </span>
            </td>
            <td class="col_type" valign="top">
                <span py:if="'label_options' in col">
                    <a href="#" style="display:block"
                        onclick="show_fk_menu('${col['other_class_name']}')"
                        id="fk_label_${col['other_class_name']}"
                        title="Change the column to use as label"
                        >${col['column_label']}</a>

                    <table cellpadding="0" cellspacing="0"
                        id="fk_menu_${col['other_class_name']}" class="column_menu"
                        border="0">
                       <tr py:for="label in col['label_options']">
                            <td>
                            <a href="#" onclick="choose_foreign_key('${col['other_class_name']}','${label['name']}')">${label['name']}</a>
                            </td>
                       </tr>
                    </table>
                </span>
            </td>
          </tr>
          </table>
      </li>
    </ul>

    </form>
    <span style="margin-top:10px">
        <button onclick="canceling()" class="blue_button" id="cancel_button"
            accesskey="c" style="margin-right:6px"><u>C</u>ancel</button>
        <button class="blue_button" onclick="saving()" accesskey="s"><u>S</u>ave</button>
    </span>

  <script>
    <![CDATA[
    function canceling()
    {
        parent.GB_hide();
    }
    function saving()
    {
        var str = '';
        for(var fk in updated_foreign_keys)
        {
            if(str!='') str+='|';
            str+= fk +':'+ updated_foreign_keys[fk];
        }
        document.columns.updated_fk_labels.value = str;

        //collect hidden columns
        var str = '';
        var elements = getElementsByTagAndClassName('img','visibility_status');
        for(var i=0;i<elements.length;i++)
        {
            var el = elements[i];
            if(el.src.indexOf('save') > 0) continue;
            if(str!='') str+='|';
            var id = el.getAttribute("id");
            id = id.replace('img_','');
            str+= id;
        }
        document.columns.hidden_columns.value= str;
        document.columns.submit();
    }
    var updated_foreign_keys={};
    var dragsort = ToolMan.dragsort();
    var junkdrawer = ToolMan.junkdrawer();
    dragsort.makeListSortable(document.getElementById('columns'),setHandle,endDrag)
    function verticalOnly(item) { item.toolManDragGroup.verticalOnly() }
    function setHandle(item) { item.toolManDragGroup.setHandle(findHandle(item)) }
    function findHandle(item) {
      var children = item.getElementsByTagName("td")
      for (var i = 0; i < children.length; i++) {
        var child = children[i]
        if (child.getAttribute("class") == null) continue
        if (child.getAttribute("class").indexOf("handle") >= 0) return child
      }
      return item
    }
    function endDrag(item)
    {
      var group = item.toolManDragGroup;
      var list = group.element.parentNode;
      var id = list.getAttribute("id");
      if (id == null) return;
      group.register('dragend', function() { store_order(id,junkdrawer.serializeList(list)) });
    }
    function store_order(id,list)
    {
        document.columns.order.value = list;
    }
    function choose_foreign_key(menu,label)
    {
        updated_foreign_keys[menu] = label;
        document.getElementById('fk_label_'+ menu).innerHTML=label;
        hide_fk_menu(menu);
    }
    function show_fk_menu(menu)
    {
        document.getElementById('fk_menu_'+menu).style.display='block'
    }
    function hide_fk_menu(menu)
    {
        document.getElementById('fk_menu_'+ menu).style.display='none';
    }
    function toggle_check(col_name)
    {
        var el = document.getElementById('img_'+ col_name);
        var img_src = el.src;
        el.src= (img_src.indexOf('transp') > 0)? img_src.replace('transp','save'):img_src.replace('save','transp');
    }
    ]]>
   </script>
</body>
</html>

