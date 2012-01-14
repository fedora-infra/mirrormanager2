var catwalk = {}
catwalk.MAX_HISTORY_LENGTH = 20;
catwalk.currentPanel = 'browse';
catwalk.multipleJoinContext = {};
catwalk.history = [];
catwalk.disclosedRelations = {};
catwalk.addHistory = function(entry)
{
    catwalk.history[catwalk.history.length]  = entry;
    if(catwalk.history.length > catwalk.MAX_HISTORY_LENGTH)
    {
        var h= catwalk.history.shift();
    }
}
catwalk.retrieveModels = function()
{
  var d = loadJSONDoc('list?_csrf_token='+fedora.identity.token);
  d.addCallback(catwalk.renderModels);
}
catwalk.renderModels = function(result)
{
  if(catwalk.error_result(result)) return;
  var models = UL({'id':'object_list'});
  for(var i=0;i < result['SQLObjects'].length;i++)
  {
    objectName = result['SQLObjects'][i];
    var model = TD(null,A({'id':'list_'+ objectName,'href':"javascript:catwalk.displayObject('"+ objectName +"')"}, objectName));
    var handle = TD({'id':'handle_'+ objectName,'class':'handle'},'\u2195');
    var mouseOver ='if(document.getElementById("handle_'+ objectName +'")) document.getElementById("handle_'+ objectName +'").style.visibility="visible"';
    var mouseOut = 'if(document.getElementById("handle_'+ objectName +'")) document.getElementById("handle_'+ objectName +'").style.visibility="hidden"';
    models.appendChild(
                        LI({'itemID':objectName,'onmouseover':mouseOver,'onmouseout':mouseOut},
                           TABLE({'border':'0','cellspacing':'2'}, TBODY(null, TR(null, handle, model) ) )
                        )
                       );
  }
  replaceChildNodes('models',models);
  dragsort.makeListSortable(document.getElementById('object_list'),setHandle,catwalk.endModelDrag)
}
catwalk.endModelDrag = function(item)
{
  var group = item.toolManDragGroup
  var list = group.element.parentNode
  var id = list.getAttribute("id")
  if (id == null) return;
  group.register('dragend', function() { catwalk.saveModelOrder(junkdrawer.serializeList(list)) });
}
catwalk.saveModelOrder = function(list)
{
  var d = loadJSONDoc('saveModelOrder?models='+list+'&_csrf_token='+fedora.identity.token);
}
catwalk.renderBoolField = function(column)
{
  var value = catwalk.getFieldValue(column); // getFieldValue return '' for default=False which works ok, but its a bit unexpected though.
  var b =  createDOM('SELECT',{'name':column.columnName});
  var t =  createDOM('OPTION',{'value':1},'True');
  var f =  createDOM('OPTION',{'value':0},'False');
  if ( value == '' || value == 'False' ) setNodeAttribute(f,'selected','selected');
  else setNodeAttribute(t,'selected','selected');
  b.appendChild(t);b.appendChild(f);
  return b;
}
catwalk.renderDate = function(fieldName,date_value,isDateTime)
{
  var pickFunc = (isDateTime)?'pickDateTime':'pickDate';
  var title = (isDateTime)? 'Choose date time, format: Year.month.day hour:minutes':'Choose date, format: Year.month.day';
  return SPAN({'class':'date_time_widget'},
               createDOM('INPUT',{'type':'text','name':fieldName,'value':date_value,'id':fieldName}),
              A({'href':'javascript:Widget.'+ pickFunc +'(\''+ fieldName +'\')',
                 'title':title},
                IMG({'border':'0','src':'/tg_widgets/turbogears.widgets/img.gif'})
               )
              );
}
catwalk.displayObject = function(objectName)
{
  switch(catwalk.currentPanel)
  {
    case 'structure':
      catwalk.retrieveStructure(objectName);
      break;
    case 'browse':
      catwalk.retrieveValues(objectName);
      break;
    case 'add':
      catwalk.retrieveFormAdd(objectName);
      break;
  }
  catwalk.hightlightObject(objectName);
}
catwalk.hightlightObject = function(objectName)
{
  var el = document.getElementById('object_list');
  var children = el.getElementsByTagName('a');
  for (var i = 0; i < children.length; i++)
  {
    var child = children[i]
    if(child.getAttribute('id') == 'list_'+ objectName)
    {
      child.style.color = '#000';
      child.style.fontWeight= '900';
    }
    else
    {
      child.style.color = '#999';
      child.style.fontWeight= '';
    }
  }
}
catwalk.retrieveStructure = function(objectName)
{
  catwalk.currentPanel='structure';
  var d = loadJSONDoc('columns?objectName='+objectName+'&_csrf_token='+fedora.identity.token);
  d.addCallback(catwalk.renderStructure);
}
catwalk.renderStructure = function(result)
{
  if(catwalk.error_result(result)) return;
  for(var i=0;i<result['columns'].length;i++)
  {
    result['columns'][i].objectName = result['objectName'];
    result['columns'][i].reorder = result['reorder'];
  }

  var s = DIV(null,
                catwalk.renderObjectMenu(result['objectName']),
                UL({'id':result['objectName'],'class':'boxy'},
                   map(catwalk.renderColumn, result['columns'])
                  )
              );
  replaceChildNodes('content',s);

  if(result['reorder'])
  {
    dragsort.makeListSortable(document.getElementById(result['objectName']),setHandle,catwalk.endDrag)
  }
  else
  {
    catwalk.retrieveColumnsForLabel(result['objectName'],
                                    result['reordering']['foreignObjectName'],
                                    result['reordering']['foreignKeyName']);
  }
  catwalk.menuSelect('structure');
}
catwalk.menuSelect = function(menu_item)
{
  document.getElementById('cell_'+ menu_item).style.backgroundColor='#999';
  document.getElementById('link_'+ menu_item).style.color='#fff';
}
catwalk.endDrag = function(item)
{
  var group = item.toolManDragGroup
  var list = group.element.parentNode
  var id = list.getAttribute("id")
  if (id == null) return;
  group.register('dragend', function() { catwalk.saveOrder(id,junkdrawer.serializeList(list)) });
}
catwalk.saveOrder = function(objectName,list)
{
  var d = loadJSONDoc('columnOrder?objectName='+ objectName +'&cols='+list+'&_csrf_token='+fedora.identity.token);
}
catwalk.renderObjectMenu = function(objectName)
{
  return  DIV
          (
            null,
            TABLE({'class':'detail_menu','cellpadding':'0','cellspacing':'0','border':'0'},
                TBODY(null,
                      TR(null,
                        TD({'id':'cell_structure'},
                           A({'id':'link_structure',
                              'title':'Display model structure (t)',
                              'accesskey':'t',
                              'href':"javascript:catwalk.retrieveStructure('"+ objectName +"')"},
                             'S', SPAN({style:'text-decoration: underline'}, 't'), 'ructure')),
                        TD({'class':'spacing'}),
                        TD({'id':'cell_browse'},
                           A({'id':'link_browse',
                              'title':'List instances (b)',
                              'accesskey':'b',
                              'href':"javascript:catwalk.retrieveValues('"+ objectName +"')"},
                             SPAN({style:'text-decoration: underline'}, 'B'), 'rowse')),
                        TD({'class':'spacing'}),
                        TD({'id':'cell_add','nowrap':'nowrap'},
                           A({'id':'link_add',
                              'title':'Add instance (a)',
                              'accesskey':'a',
                              'href':"javascript:catwalk.retrieveFormAdd('"+ objectName +"')"},
                             SPAN({style:'text-decoration: underline'}, 'A'),'dd '+ objectName)),
                        TD({'class':'spacing','style':'width:300px'})
                      )
                )
             )
          );
}
catwalk.columnLabel = function(col)
{
  var columnName = col.columnName;
  if(col.title!='') columnName = SPAN(null,col.title, SPAN({'style':'font-size:9px;color:#cdcdcd'},' ['+ columnName +']'));
  return columnName;
}
catwalk.renderColumn = function(col)
{
  var label = TD({'class':'label'},catwalk.columnLabel(col) );
  var fieldType = TD({'class':'coltype'},col.type);

  if(col.type == 'SOForeignKey' || col.type == 'SOSingleJoin')
  {
    fieldType = TD({'class':'coltype'},
                   SPAN(null,col.type +':'),
                   A( {'href':"javascript:catwalk.displayObject('"+ col.join +"')"},col.join),
                   SPAN(null,', label column:'),
                   SPAN({'id':'spanid_'+ col.columnName },
                   A( {'href':"javascript:catwalk.columnsForLabelView('"+ col.objectName +"','"+ col.join +"','"+ col.columnName +"')"},col.labelColumn)
                  )
                );
  }
  if(col.type=='SOMultipleJoin' || col.type=='SOSQLMultipleJoin')
  {
    fieldType = TD({'class':'coltype'},
                   SPAN(null,col.type +':'),
                   A( {'href':"javascript:catwalk.displayObject('"+ col.join +"')"},col.join)
                  );
  }
  var handle = (col.reorder)? TD({'id':'handle_'+ col.columnName,'class':'handle'},'\u2195'):TD({'id':'handle_'+ col.columnName});

  var mouseOver ='document.getElementById("handle_'+ col.columnName +'").style.visibility="visible"';
  var mouseOut = 'document.getElementById("handle_'+ col.columnName +'").style.visibility="hidden"';

  return LI({'itemID':col.columnName,'onmouseover':mouseOver,'onmouseout':mouseOut},
             TABLE({'border':'0','cellspacing':'0'},
                   TBODY(null, TR(null, handle, label,fieldType) )
                  )
           );
}
catwalk.columnsForLabelView = function(objectName,foreignObjectName,foreignKeyName)
{
  catwalk.currentPanel='structure';
  var url='columns?objectName='+objectName;
  url+='&foreignObjectName='+ foreignObjectName +'&foreignKeyName='+ foreignKeyName;
  url+='&_csrf_token='+fedora.identity.token;
  var e = loadJSONDoc(url);
  e.addCallback(catwalk.renderStructure);
}
catwalk.retrieveColumnsForLabel = function(objectName,foreignObjectName,foreignKeyName)
{
  var url='columnsForLabel?objectName='+objectName;
  url+='&foreignObjectName='+ foreignObjectName +'&foreignKeyName='+ foreignKeyName;
  url+='&_csrf_token='+fedora.identity.token;
  var e = loadJSONDoc(url);
  e.addCallback(catwalk.renderColumnsForLabel);
}
catwalk.renderColumnsForLabel = function(result)
{
  if(catwalk.error_result(result)) return;
  var options = [{'selected':true,'value':'id','label':'id'}];
  for(var i=0;i<result['columns'].length;i++)
  {
    selected = ( result['foreignKeyColumnForLabel'] == result['columns'][i].columnName);
    label = result['columns'][i].columnName;
    if(result['columns'][i].title !='') label = result['columns'][i].title +' ('+ label +')';
    options[options.length] = {'selected':selected,
                               'value':result['columns'][i].columnName,
                               'label':label
                               };
  }
  var action = "catwalk.selectColumnForLabel(this,";
  action += "'"+ result['objectName'] +"','"+ result['foreignObjectName'] +"','"+ result['foreignKeyName'] +"'";
  action += ")";
  var labelChooser = createDOM('SELECT',
                               {'onchange':action},
                                map(catwalk.renderOptions, options)
                              );
  replaceChildNodes('spanid_'+ result['foreignKeyName'],labelChooser);
}
catwalk.selectColumnForLabel = function(columnList,objectName,foreignObjectName,foreignKeyName)
{
  var columnName = columnList.options[columnList.selectedIndex].value;
  var url= 'setColumnForLabel?objectName='+objectName;
  url+='&foreignObjectName='+ foreignObjectName;
  url+='&foreignKeyName='+ foreignKeyName;
  url+='&columnName='+ columnName;
  url+='&_csrf_token='+fedora.identity.token;
  var e = loadJSONDoc(url);
  e.addCallback(catwalk.renderStructure);
}
catwalk.browse = function(object_name,start,page_size)
{
  catwalk.currentPanel='browse';
  var url = 'browse?object_name='+ object_name;
  url+='&_csrf_token='+fedora.identity.token;
  if(start) url+='&start='+ start;
  if(page_size) url+='&page_size='+ page_size;

  catwalk.addHistory({'view':'browse','objectName':object_name});
  var e = doSimpleXMLHttpRequest(url);
  e.addCallback(catwalk.insert_grid);
}
catwalk.retrieveValues = function(object_name,start,page_size)
{
  if(!start) start = 0;
  catwalk.currentPanel='browse';
  var url = 'browse?object_name='+ object_name;
  url+='&_csrf_token='+fedora.identity.token;
  if(start) url+='&start='+ start;
  if(page_size) url+='&page_size='+ page_size;
  catwalk.addHistory({'view':'browse','objectName':object_name});

  var e = doSimpleXMLHttpRequest(url);
  e.addCallback(catwalk.insert_grid);
}
catwalk.insert_grid = function(request)
{
  document.getElementById('content').innerHTML = request.responseText;
}
catwalk.error_result = function(result)
{
  if(!Widget.exists(result.error)) return false;
  return true;
}
catwalk.paging_footer = function(result)
{
    var total = parseInt(result['total']);
    var start = parseInt(result['start']);
    var size = parseInt(result['page_size']);
    if(total <= size ) return '';
    var page_number = parseInt( start / size + 1 );
    var total_pages =  parseInt( total/size +1);
    var previous_page = IMG({'border':'0','style':'margin-right:5px','align':'absbottom',
                                'src':tg_static_directory +'/images/transp.png'} );
    var next_page = previous_page;
    var next_start = start + size;
    var previous_start = start - size;
    if(page_number > 1)
    {
        previous_page = A({
                           'href':"javascript:catwalk.retrieveValues('"+ result['objectName'] +"','"+ previous_start +"')",
                           'title':'Previous page',
                           'class':'discloser'
                           },
                           IMG({'border':'0','width':'15','style':'margin-right:5px','align':'absbottom',
                                'src':tg_static_directory +'/images/arrow_left.png'} )
                          );
    }
    if(page_number < total_pages)
    {
        next_page = A({
                           'href':"javascript:catwalk.retrieveValues('"+ result['objectName'] +"','"+ next_start +"')",
                           'title':'Next page',
                           'class':'discloser'
                           },
                           IMG({'border':'0','style':'margin-right:5px','align':'absbottom',
                                'src':tg_static_directory +'/images/arrow_right.png'} )
                          );
    }
    return DIV({'style':'font-size:10px;margin:6px;'},
               previous_page,
               ' ',
               'Page ',
               catwalk.page_selector(page_number,total_pages,size,result['objectName']) ,
               '  of '+ total_pages,
               ' ',
               next_page
              );
}
catwalk.page_size = function(size,object_name)
{
    var page_size =  createDOM('SELECT',{'style':'font-size:10px',
                                         'onchange':'catwalk.update_page_size(this,"'+ object_name +'")'});
    var sizes= [10,20,50,70,100,200,300,500,700,900];
    for(var i=0;i < sizes.length;i++)
    {
        var props ={'value':(sizes[i])};
        if(sizes[i] == size) props['selected'] ='selected';
        page_size.appendChild(createDOM('OPTION',props,sizes[i] ));
    }
    return page_size;
}
catwalk.page_selector = function(page_number,total_pages,size,object_name)
{
    var page_selector =  createDOM('SELECT',{'style':'font-size:10px',
                                             'onchange':'catwalk.update_page(this,"'+ object_name +'")'});
    for(var i=0;i < total_pages;i++)
    {
        var props ={'value':(i*size)};
        if((i+1) == page_number) props['selected'] ='selected';
        page_selector.appendChild(createDOM('OPTION',props,(i+1)));
    }
    return page_selector;
}
catwalk.update_page_size = function(list,object_name)
{
    return;
}
catwalk.update_page = function(list,object_name)
{
    var page = list.options[list.selectedIndex].value;
    catwalk.retrieveValues(object_name,page);
}
catwalk.renderValues = function(result)
{
  if(catwalk.error_result(result)) return;
  var data = { 'headers':result['headers'],
               'rows':result['rows'],
               'hidden_columns':(Widget.exists(result['hidden_columns']))? result['hidden_columns']:[],
               'actions':{
                          'sort':'',
                          'column_management':{'function':'catwalk.updateColumns','params':[result['objectName']]},
                          'select':{'function':'catwalk.retrieveDisplayObject','params':[result['objectName']]},
                          'edit':{'function':'catwalk.retrieveFormEdit','params':[result['objectName']]},
                          'remove':{'function':'catwalk.retrieveRemove','params':[result['objectName']]}
                          }
             };

  var grid = Widget.grid.render(result['objectName'],data);
  replaceChildNodes('content', DIV(null,
                                   catwalk.renderObjectMenu(result['objectName']),
                                   grid,
                                   catwalk.paging_footer(result)
                                  )
                    );
  catwalk.menuSelect('browse');
  catwalk.addHistory({'view':'browse','objectName':result['objectName']});
}
catwalk.retrieveContinueFormAdd = function(result)
{
  if(catwalk.error_result(result)) return;
  catwalk.retrieveFormAdd(result['objectName']);
}
catwalk.retrieveFormAdd = function(objectName)
{
  catwalk.currentPanel='add';
  var d = loadJSONDoc('columns?objectName='+objectName+'&_csrf_token='+fedora.identity.token);
  d.addCallback(catwalk.renderFormAdd);
}
catwalk.submiting = function()
{
   return false;
}
catwalk.renderFormAdd = function(result)
{
  if(catwalk.error_result(result)) return;
  var objectName = result['objectName'];

  var cancelButton = catwalk.renderButton('btnCancel',
										  [SPAN({style: 'text-decoration: underline'}, 'C'), 'ancel', ''],
                                          'catwalk.historyBack()',
                                          'Cancel (c)',
                                          'c'
                                          );

  var saveAndAdd = catwalk.renderButton('btnSaveAndAdd',
                                        ['Save and add another ', SPAN({style: 'text-decoration: underline'}, '+')],
                                        "catwalk.retrieveObjectCreate('"+ objectName +"','save_and_add')",
                                        'Save and add another (+)',
                                        '+'
                                       );
  var save = catwalk.renderButton('btnSave',
                                  [SPAN({style: 'text-decoration: underline'}, 'S'),'ave',''],
                                  "catwalk.retrieveObjectCreate('"+ objectName +"','save')",
                                  'Save (s)',
                                  's'
                                  )
  var formAdd = createDOM('DIV',null,
                           catwalk.renderObjectMenu(objectName),
                           catwalk.renderObjectColumns(result['columns'],catwalk.renderFormColumn),
                           cancelButton,
                           saveAndAdd,
                           save
                          );
  replaceChildNodes('content',formAdd);
  catwalk.focusOnFirstStringField();
  catwalk.setMultipleJoinContext();
  catwalk.addHistory({'view':'add','objectName':objectName});
  catwalk.menuSelect('add');
}
catwalk.setMultipleJoinContext = function()
{
    if(!Widget.exists(catwalk.multipleJoinContext['id']) ) return;
    if(!Widget.exists(catwalk.multipleJoinContext['hostObject']) ) return;
    var fieldName = 'foreign_key_'+ catwalk.multipleJoinContext['hostObject'];
    var el = document.getElementById(fieldName);
    if(!Widget.exists(el)) return;
    for(var i=0;i<el.options.length;i++)
    {
        if(el.options[i].value == catwalk.multipleJoinContext['id'])
        {
            el.options[i].selected=true;
            return;
        }
    }
}
catwalk.renderButton = function(btnId,label,action,title,accesskey)
{
  var props = {'class':'buts',
               'id':btnId,
               'onclick':action
              };
  if(Widget.exists(title)) props['title'] = title;
  if(Widget.exists(accesskey)) props['accesskey'] = accesskey;
  return createDOM('BUTTON',props, label[0], label[1], label[2]);
}
catwalk.renderFormColumn = function(column)
{
  if(column.type.match(/\b(SO)+\w+(Join)+\b/)) return; //ignore any type of join
  if(Widget.exists(column.value) && Widget.exists(column.value.value)) column.value = column.value.value;
  var columnValue;
  switch(column.type)
  {
    case 'SOUnicodeCol':
      columnValue = catwalk.renderStringColumn(column);
      break;
    case 'SOStringCol':
      columnValue = catwalk.renderStringColumn(column);
      break;
    case 'SOForeignKey':
      columnValue = catwalk.renderForeignKeyColumn(column);
      break;
    case 'SOIntCol':
      columnValue = catwalk.renderNumericCol(column,'int');
      break;
    case 'SODecimalCol':
      columnValue = catwalk.renderNumericCol(column,'float');
      break;
    case 'SOFloatCol':
      columnValue = catwalk.renderNumericCol(column,'float');
      break;
    case 'SOBoolCol':
      columnValue = TD(null, catwalk.renderBoolField(column));
      break;
    case 'SOEnumCol':
      columnValue =  TD(null,catwalk.renderEnumCol(column));
      break;
    case 'SODateCol':
      var value = column.value;
      if(!Widget.exists(value)) value = (Widget.exists(column['default']))? column['default']:'';
      columnValue =  TD(null,catwalk.renderDate(column.columnName,value,false));
      break;
    case 'SODateTimeCol':
      var value = column.value;
      if(!Widget.exists(value)) value = (Widget.exists(column['default']))? column['default']:'';
      columnValue = TD(null,catwalk.renderDate(column.columnName,value,true));
      break;
    default:
      columnValue = TD(null, createDOM('INPUT',{'class':'txtfield','type':'text','name':column.columnName}) );
  }
  return TR(null, TD({'valign':'top'}, SPAN({'class':'previewLabel'},catwalk.columnLabel(column)) ), columnValue);
}
catwalk.renderForeignKeyColumn = function(column)
{
  for(var i=0;i<column.options.length;i++)
  {
    column.options[i] = (Widget.exists(column.id) && column.options[i].id ==column.id.value)? {
                                                             'selected':true,
                                                             'value':column.options[i].id,
                                                             'label':column.options[i].label
                                                             }:{
                                                               'selected':false,
                                                               'value':column.options[i].id,
                                                               'label':column.options[i].label
                                                             };
  }
  var sel_id = 'foreign_key_'+ column.join;
  return TD(null,
            createDOM('SELECT',
                      {'id':sel_id,'name':column.columnName},
                      map(catwalk.renderOptions, column.options)
                     )
           );
}

catwalk.renderEnumCol = function(column)
{
  for(var i=0;i<column.options.length;i++)
  {
    column.options[i] = {
                         'selected':(column.options[i] ==column.value),
                         'value':column.options[i],
                         'label':column.options[i]
                        }
  }
  return TD({'style':'border-bottom:none'},
            createDOM('SELECT',
                      {'name':column.columnName},
                      map(catwalk.renderOptions, column.options)
                     )
           );
}
catwalk.getValueForField = function(form,fieldName)
{
  for(var i=0; i<form.elements.length;i++)
  {
    if(form.elements[i].name==fieldName) return form.elements[i].value;
  }
  return '';
}
catwalk.getFieldNameForDate = function(field)
{
  fieldName = field.split('_');
  return fieldName[1];
}
catwalk.collectPostVars = function(f)
{
  var postVars='';
  for(var i=0; i<f.elements.length;i++)
  {
    var t = f.elements[i].type;
    if(t.indexOf('text') > -1 )
    {
      if(postVars!='') postVars+='&';
      postVars+= f.elements[i].name +'='+ encodeURIComponent(f.elements[i].value);
    }
    if(t.indexOf('select') > -1)
    {
      if(postVars!='') postVars+='&';
      postVars+= f.elements[i].name +'='+ f.elements[i].options[f.elements[i].selectedIndex].value;
    }
  }
  return postVars;
}
catwalk.retrieveObjectCreate = function(objectName,whereToGo)
{
  var postVars = catwalk.collectPostVars(document.myform);
  postVars+= '&objectName='+ objectName;
  postVars+='&_csrf_token='+fedora.identity.token;
  var d = postJSONDoc('add',postVars);

  d.addCallbacks(notify_success, notify_warning);
  d.addCallback((whereToGo=='save')? catwalk.savedObject:catwalk.retrieveContinueFormAdd);
}
catwalk.getLastDisplayView = function()
{
    //check if the last displayed object was a parent object
    for(var i=(catwalk.history.length-1);i>= 0;i--)
    {
        if(catwalk.history[i]['view']=='display')
        {
            return catwalk.history[i];
        }
    }
    return false;
}
catwalk.savedObject = function(result)
{
    var view = catwalk.getLastDisplayView();
    if(!Widget.exists(catwalk.multipleJoinContext['id']) || !view )
    {
        catwalk.renderDisplayObject(result);
        return;
    }
    if(catwalk.multipleJoinContext['hostObject']==view['objectName'])
    {
       catwalk.retrieveDisplayObject(view['objectName'],view['id']);
       return;
    }
    catwalk.renderDisplayObject(result);
}
catwalk.retrieveDisplayObject = function(objectName,id)
{
  var e = loadJSONDoc('instance?objectName='+objectName+'&id='+id+'&_csrf_token='+fedora.identity.token);
  e.addCallback(catwalk.renderDisplayObject);
}
catwalk.historyBack = function()
{
    if(catwalk.history.length==1) return;
    var step = catwalk.history.pop(); //pop the current view first..
    step = catwalk.history.pop(); //get the previous view

    switch(step['view'])
    {
       case 'browse':
        catwalk.browse(step['objectName']);
        break;
       case 'display':
        catwalk.retrieveDisplayObject(step['objectName'],step['id']);
        break;
       case 'edit':
        catwalk.historyBack();
        break;
       case 'add':
        catwalk.historyBack();
        break;
    }
}
catwalk.renderDisplayObject= function(result)
{
  if(catwalk.error_result(result)) return;
  catwalk.multipleJoinContext= {};
  var objectName = result['objectName'];

  var cancelButton = catwalk.renderButton('btnCancel',
                                          [SPAN({style: 'text-decoration: underline'}, 'C'),'ancel',''],
                                          "catwalk.historyBack()",
                                          'Cancel (c)',
                                          'c'
                                          );

  var editButton = catwalk.renderButton('btnEdit',
                                        [SPAN({style: 'text-decoration: underline'}, 'E'),'dit',''],
                                        "catwalk.retrieveFormEdit('"+ objectName +"','"+ result['id'] +"')",
                                        'Edit (e)',
                                        'e'
                                        );
  var formEdit = createDOM('DIV',null,
                            catwalk.renderObjectMenu(objectName) ,
                            catwalk.renderObjectColumns(result['values'],catwalk.renderDisplayColumn),
                            cancelButton,
                            editButton
                          );
  replaceChildNodes('content',formEdit);
  catwalk.menuSelect('browse');
  catwalk.addHistory({'view':'display','objectName':objectName,'id':result['id']});
  catwalk.hightlightObject(objectName);
  catwalk.checkDisclosedRelations(objectName,result['id']);
}
catwalk.checkDisclosedRelations = function(objectName,id)
{
    for(joinName in catwalk.disclosedRelations)
    {
        var ctx = catwalk.disclosedRelations[joinName];
        if(!ctx['visible']) continue;
        if(ctx['objectName']!=objectName) continue;
        if(ctx['id']!=id) continue;
        var disclose = document.getElementById('disclose_'+ joinName);
        if(disclose ==null || disclose == undefined) continue;
        catwalk.retrieveJoins(ctx['objectName'],
                              ctx['id'],
                              ctx['joinName'],
                              ctx['joinType'],
                              ctx['joinObjectName']);
    }
}
catwalk.retrieveManageRelatedJoins = function(objectName,id,joinName,relatedObjectName)
{
  var params = 'objectName='+ objectName +'&id='+ id +'&join='+ joinName;
  params+='&relatedObjectName='+ relatedObjectName;
  params+='&_csrf_token='+fedora.identity.token;
  var e = loadJSONDoc('manageRelatedJoins?'+ params);
  e.addCallback(catwalk.renderManageRelatedJoins);
}
catwalk.optionsForJoins = function(rows)
{
  var options = [];
  for(var i=0;i<rows.length;i++)
  {
    var values='';
    for(var j=0;j<rows[i].length;j++)
    {
      if(values!='')values+=',';
      values+=rows[i][j].value;
    }
    options[options.length] = {'selected':false,'value':rows[i][0].value,'label':values };
  }
  return options;
}
catwalk.renderManageRelatedJoins = function(results)
{
  if(catwalk.error_result(results)) return;
  var thisJoins = createDOM('SELECT',
                                {'id':'select_remove_'+ results['join'],'size':'10','style':'width:225px','multiple':'multiple'},
                                map(catwalk.renderOptions, catwalk.optionsForJoins(results['rows']) )
                           );
  var allJoins = createDOM('SELECT',{'id':'select_add_'+ results['join'],'size':'10','style':'width:225px','multiple':'multiple'},
                                map(catwalk.renderOptions, catwalk.optionsForJoins(results['allJoins']['rows']) )
                           );
  var params = [results['hostObject'],results['id'],results['join'],results['joinType'],results['joinObjectName']];
  var joinsTable = TABLE(null,
                         TBODY(null,
                               TR(null,
                                  TD({'style':'border:none'},thisJoins),
                                  TD({'style':'border:none'},allJoins)
                                 ),
                               TR(null,
                                  TD({'style':'border:none'},
                                     Widget.iconLabel.render('remove','Remove Selected','javascript:catwalk.removeSelectedJoins',[results['join']])
                                    ),
                                  TD({'style':'border:none'},
                                     Widget.iconLabel.render('add','Add Selected','javascript:catwalk.addSelectedJoins',[results['join']])
                                    )
                                 ),
                                TR(null,
                                  TD({'style':'border:none','colspan':'2','align':'right'},
                                      Widget.iconLabel.render('discard','Discard','javascript:catwalk.retrieveJoins',params),
                                      Widget.iconLabel.render('save','Save','javascript:catwalk.saveJoins',params)
                                    )
                                )
                               )
                         );
  replaceChildNodes('grid_'+ results['join'],joinsTable );
}
catwalk.removeSelectedJoins= function(join)
{
  var list = document.getElementById('select_remove_'+ join);
  Widget.select.removeSelectedOptions(list);
}
catwalk.addSelectedJoins= function(join)
{
  var src = document.getElementById('select_add_'+ join);
  var dest = document.getElementById('select_remove_'+ join);
  Widget.select.addSelectedOptionsFromSourceToDestination(src,dest);
}
catwalk.saveJoins = function(objectName,id,joinName,joinType,joinObjectName)
{
  var u = 'updateJoins?objectName='+ objectName +'&id='+ id;
  u+='&join='+ joinName +'&joinType='+ joinType +'&joinObjectName='+ joinObjectName;
  u+='&joins='+ Widget.select.getOptionValuesAsCSV( document.getElementById('select_remove_'+ joinName) );
  u+='&_csrf_token='+fedora.identity.token;
  var e = loadJSONDoc(u);
  e.addCallbacks(notify_success, notify_warning);
  e.addCallback(catwalk.renderDisplayObject);
}
catwalk.addDisclosedRelation= function(joinName,context)
{
    catwalk.disclosedRelations[joinName]=context;
}
catwalk.toggleDisclosedRelation= function(joinName)
{
    catwalk.disclosedRelations[joinName]['visible'] = !catwalk.disclosedRelations[joinName]['visible'];
}
catwalk.retrieveJoins= function(objectName,id,joinName,joinType,joinObjectName)
{
  var u = 'joins?objectName='+ objectName +'&id='+ id;
  u+='&join='+ joinName +'&joinType='+ joinType +'&joinObjectName='+ joinObjectName;
  u+='&_csrf_token='+fedora.identity.token;
  catwalk.addDisclosedRelation(joinName,{'objectName':objectName,
                                         'visible':true,
                                         'id':id,
                                         'joinName':joinName,
                                         'joinType':joinType,
                                         'joinObjectName':joinObjectName});
  var e = loadJSONDoc(u);
  e.addCallback(catwalk.renderJoins);
}
catwalk.toggleJoins = function(joinName)
{
  var e = document.getElementById('grid_'+ joinName);
  e.style.display= (e.style.display=='')? 'none':'';
  var arrow =(e.style.display=='')? 'down':'right';
  var newLink = A({
                   'href':"javascript:catwalk.toggleJoins('"+ joinName +"')",
                   'title':(e.style.display=='')? 'Hide join values':'Show join values',
                   'class':'discloser'
                   },
                   IMG({'border':'0','style':'margin-right:5px','align':'bottom',
                        'src':tg_static_directory +'/images/arrow_'+ arrow +'.png'} )
                  );
  replaceChildNodes('disclose_'+ joinName,newLink);
  catwalk.toggleDisclosedRelation(joinName);
}
catwalk.renderJoins = function(results)
{
  if(catwalk.error_result(results)) return;
  var params = [results['hostObject'], results['id'],
                results['join'],results['joinType'],
                results['joinObjectName']
               ];


  var data = { 'headers':results['headers'],
               'rows':results['rows'],
               'hidden_columns':(Widget.exists(results['hidden_columns']))? results['hidden_columns']:[],
               'actions':{
                          'sort':'',
                          'column_management':{'function':'catwalk.updateColumnsJoinView','params':params},
                          'select':{'function':'catwalk.retrieveDisplayObject','params':[results['objectName']]},
                          'edit':{'function':'catwalk.retrieveFormEdit','params':[results['objectName']]},
                          'remove':{'function':'catwalk.retrieveRemove','params':[results['objectName']]}
                          }
             };
  //this is causing trouble in related joins...
  //if(results['joinType']=='SORelatedJoin') data['actions']['remove']='';

  var grid = (results['rows'].length >0)? Widget.grid.render(results['join'],data):'';
  var r = results;
  if(results['joinType']=='SORelatedJoin' ||
    results['joinType']=='SOSQLRelatedJoin')
  {
    grid = DIV(null,grid,catwalk.renderManageRelatedControl(r['hostObject'],r['id'],r['join'],r['joinObjectName']));
  }
  else
  {
    //grid = DIV(null,grid,catwalk.renderAddMultipleJoinsControl(r['joinObjectName']));
    grid = DIV(null,grid,catwalk.renderAddMultipleJoinsControl(r['hostObject'],r['id'],r['joinObjectName']));
  }
  replaceChildNodes('grid_'+ results['join'],grid);

  var newLink = A({
                   'href':"javascript:catwalk.toggleJoins('"+ results['join'] +"')",
                   'title':'Hide join values',
                   'class':'discloser'
                   },
                   IMG({'border':'0','style':'margin-right:5px','align':'absbottom',
                        'src':tg_static_directory +'/images/arrow_down.png'} )
                  );
  replaceChildNodes('disclose_'+ results['join'],newLink);
}
catwalk.updateColumns = function(objectName,column)
{
  var u = 'updateColumns?objectName='+ objectName +'&column='+ column;
  var e = loadJSONDoc(u);
  e.addCallback(catwalk.renderValues);
}
catwalk.updateColumnsJoinView= function(objectName,id,join,joinType,joinObjectName,column)
{
  var u = 'updateColumnsJoinView?objectName='+ objectName +'&id='+ id;
  u+='&join='+ join +'&joinType='+ joinType +'&joinObjectName='+ joinObjectName;
  u+='&column='+ column;
  var e = loadJSONDoc(u);
  e.addCallback(catwalk.renderJoins);
}
catwalk.addSingleJoin = function(hostObject,id,otherClassName)
{
    catwalk.multipleJoinContext = {'hostObject':hostObject,'id':id};
    catwalk.retrieveFormAdd(otherClassName);
}
catwalk.addMultipleJoin = function(hostObject,id,otherClassName)
{
    catwalk.multipleJoinContext = {'hostObject':hostObject,'id':id};
    catwalk.retrieveFormAdd(otherClassName);
}
catwalk.renderAddMultipleJoinsControl = function(hostObject,id,otherClassName)
{
  return Widget.iconLabel.render('add','Add Multiple Join',
                                 'javascript:catwalk.addMultipleJoin',[hostObject,id,otherClassName]);
}
catwalk.renderManageRelatedControl = function(objectName,id,joinMethodName,otherClassName)
{
  return Widget.iconLabel.render('edit','Manage Relations',
                                 'javascript:catwalk.retrieveManageRelatedJoins',
                                 [objectName,id,joinMethodName,otherClassName]);
}
catwalk.renderDisplayColumn = function(column)
{
  var label = SPAN({'class':'previewLabel'},catwalk.columnLabel(column) );
  var val = column.value.value;
  if(column.type=='SOSingleJoin')
  {
    if(val=='None'||val=='')
    {
        val = Widget.iconLabel.render('add','Add Single Join',
                                      'javascript:catwalk.addSingleJoin',
                                      [column.objectName,column.object_id,column.join]);
    }
    else
    {
        val = SPAN(null,val,
                   Widget.iconLabel.render('discard','',
                                           'javascript:catwalk.discardSingleJoin',
                                           [column.objectName,column.object_id,column.join,column.id.value]) );
    }
  }
  if(column.type=='SOMultipleJoin' || column.type=='SOSQLMultipleJoin' ||
    column.type=='SORelatedJoin' || column.type=='SOSQLRelatedJoin')
  {
    var edit = '';
    var action = Widget.renderHandler('javascript:catwalk.retrieveJoins',
                                      [column.objectName,column.object_id,column.columnName,column.type,column.join]
                                     );
    return TR(null, TD({'colspan':'2'},
                        SPAN({'id':'disclose_'+ column.columnName},
                          A({
                             'href':action,
                             'title':'Display join values',
                             'class':'discloser'
                             },
                             IMG({'border':'0','style':'margin-right:5px','align':'bottom',
                                  'src':tg_static_directory +'/images/arrow_right.png'} )
                            )
                        ),
                       label,
                       '  ('+ catwalk.joinLabel(val) +')  ',
                       edit,
                        DIV({'class':'multiplejoin','id':'grid_'+ column.columnName})
                       )
              );
  }
  return TR(null, TD(null,label), TD(null,val));
}
catwalk.discardSingleJoin = function(objectName,id,join_object_name,join_object_id)
{
    if(!confirm('Are you sure you want to delete the single join?')) return;
    var e = loadJSONDoc('remove_single_join?object_name='+
                         objectName+'&id='+
                         id+'&join_object_name='+
                         join_object_name +'&join_object_id='+ join_object_id +
			'&_csrf_token='+fedora.identity.token);
    e.addCallback(catwalk.renderDisplayObject);
}
catwalk.joinLabel = function(value)
{
  var n = parseInt(value);
  if(isNaN(n)) n = 0;
  n+= (n ==1 )? ' Row':' Rows';
  return n
}
catwalk.renderObjectColumns = function(values,mapFunction)
{
  return TABLE({'class':'detail_grid','cellpadding':'5'}, TBODY(null, map(mapFunction,values) ) );
}
catwalk.retrieveFormEdit = function(objectName,id)
{
  var e = loadJSONDoc('instance?objectName='+objectName+'&id='+id+'&_csrf_token='+fedora.identity.token);
  e.addCallback(catwalk.renderFormEdit);
}
catwalk.renderFormEdit = function(result)
{
  if(catwalk.error_result(result)) return;
  var objectName = result['objectName'];

  var cancelButton = catwalk.renderButton('btnCancel',
                                          [SPAN({style: 'text-decoration: underline'}, 'C'),'ancel',''],
                                          'catwalk.historyBack()',
                                          'Cancel (c)',
                                          'c'
                                          );

  var updateButton = catwalk.renderButton('btnUpdate',
                                    ['Update (',SPAN({style: 'text-decoration: underline'}, 's'),')'],
                                    "catwalk.retrieveObjectUpdate('"+ objectName +"','"+ result['id'] +"')",
                                    'Update (s)',
                                     's'
                                    );

  var formEdit = createDOM('DIV',null,
                            catwalk.renderObjectMenu(objectName) ,
                            catwalk.renderObjectColumns(result['values'],catwalk.renderFormColumn),
                            cancelButton,
                            updateButton
                          );
  replaceChildNodes('content',formEdit);
  catwalk.focusOnFirstStringField();
  catwalk.addHistory({'view':'edit','objectName':objectName,'id':result['id']});
  catwalk.menuSelect('browse');
}
catwalk.focusOnFirstStringField = function()
{
    var f = document.myform;
    for(var i=0; i<f.elements.length;i++)
    {
        var t = f.elements[i].type;
        if(t.indexOf('text') > -1 )
        {
            f.elements[i].select();
            f.elements[i].focus();
            return;
        }
    }
}
catwalk.renderOptions = function(option)
{
  if(option.selected) return createDOM('OPTION',{'value':option.value,'selected':'selected'},option.label);
  return createDOM('OPTION',{'value':option.value},option.label);
}
catwalk.renderStringColumn = function(column)
{
  if(column.length != null && column.length > 0)
  {
    return TD(null, createDOM('INPUT',
                              {'class':'txtfield',
                               'type':'text',
                               'name':column.columnName,
                               'value':catwalk.getFieldValue(column),
                               'maxlength':column.length
                              }
                             )
             );
  }

  return TD(null, createDOM('TEXTAREA',
                             {'name':column.columnName, 'class':'txtarea'},
                              catwalk.getFieldValue(column)
                           )
           );
}
catwalk.validate = function(field,expectedType,notNone)
{
  if (field.value || notNone) {
    switch(expectedType)
    {
      case 'int':
        if(isNaN(parseInt(field.value))) field.value = field.defaultValue;
      case 'float':
        if(isNaN(parseFloat(field.value))) field.value = field.defaultValue;
    }
  }
}
catwalk.getFieldValue = function(column)
{
  var value = (Widget.exists(column.value))? column.value:'';
  if(!Widget.exists(value)) value = (Widget.exists(column['default']))? column['default']:'';
  return value;
}
catwalk.renderNumericCol = function(column,digitType)
{
  return TD(null, createDOM('INPUT',
                            {'class':'txtfield',
                             'type':'text',
                             'name':column.columnName,
                             'value':catwalk.getFieldValue(column),
                             'onblur':'catwalk.validate(this,"'+ digitType +'",' + column.notNone + ')'
                            }
                           )
           );
}
catwalk.updated = function(results)
{
    catwalk.historyBack();
}
catwalk.retrieveObjectUpdate = function(objectName,id)
{
  var postVars =catwalk.collectPostVars(document.myform);
  postVars+= '&objectName='+ objectName +'&id='+ id;
  postVars+='&_csrf_token='+fedora.identity.token;

  var d = postJSONDoc('update',postVars);
  d.addCallbacks(notify_success, notify_warning);
  d.addCallback(catwalk.updated);
}
function postJSONDoc(url,postVars)
{
  var req = getXMLHttpRequest();
  req.open('POST',url,true);
  req.setRequestHeader('Content-type','application/x-www-form-urlencoded');
  var data = postVars;
  var d = sendXMLHttpRequest(req,data);
  return d.addCallback(evalJSONRequest);
}
catwalk.removedRow = function(result)
{
    if(catwalk.history.length < 1)
    {
        catwalk.browse(result['objectName']);
        return;
    }
    var step = catwalk.history[catwalk.history.length-1];
    if(step['view']=='display')
    {
        catwalk.retrieveDisplayObject(step['objectName'],step['id']);
        return;
    }
    catwalk.browse(result['objectName']);
}
catwalk.retrieveRemove= function (objectName,id)
{
  if(!confirm('Are you sure you want to remove the object '+ objectName +':'+ id +'?')) return;
  var url='&_csrf_token='+fedora.identity.token;
  var d = postJSONDoc('remove','objectName='+objectName+'&id='+ id+url);
  d.addCallbacks(notify_success, notify_warning);
  d.addCallback(catwalk.removedRow);
}
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
var dragsort = ToolMan.dragsort()
var junkdrawer = ToolMan.junkdrawer()
