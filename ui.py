import os, math

from pyfbsdk import *
from pyfbsdk_additions import *
from PySide2 import QtWidgets

os.sys.path.append(os.path.dirname(__file__))
import mb_retarget as mbr
import importlib
importlib.reload(mbr)



src_data_list  = []
tgt_model_list = []


### Functions
def OnUnbind(control, event):
    global t
    FBDestroyTool(t)


def OpenFolderExplorer(search_e, lyt_data_list=None, list_type=None):
    file_path = QtWidgets.QFileDialog.getExistingDirectory(None, "Select Directory", search_e.Text)
    if file_path == "":
        file_path = search_e.Text
    search_e.Text = file_path

    if lyt_data_list is not None and list_type is not None:
        global src_data_list, tgt_model_list
        if list_type == "source":
            src_data_list = UpdateDataList(file_path, lyt_data_list)
            UpdateMaxBatchNum(len(src_data_list))
        elif list_type == "target":
            tgt_model_list = UpdateDataList(file_path, lyt_data_list)


def GetSelectedDataNames(data_list):
    selected_data = []
    for i in range(len(data_list)):
        if data_list[i].State:
            selected_data.append(data_list[i].Caption)

    print(selected_data)
    return selected_data


def LoadData(data_path):
    data_list = os.listdir(data_path)
    data_list = [x for x in data_list if x.endswith(".fbx") or x.endswith(".bvh")]
    data_list = [x.split(".")[0] for x in data_list]
    data_list.sort()

    return data_list


def ClampValue(edit_text, min_value=1, max_value=math.inf):   
    edit_text.Value = max(min_value, edit_text.Value)

    if max_value > min_value and max_value != math.inf:
        edit_text.Value = min(max_value, edit_text.Value)


def UpdateMaxBatchNum(num):
    global max_batch_num
    max_batch_num = num


def UpdateSourceTargetList(src_data_path, lyt_src_data_list,
                           tgt_data_path, lyt_tgt_model_list):
    
    global src_data_list, tgt_model_list
    # update data list
    src_data_list  = UpdateDataList(src_data_path, lyt_src_data_list)
    tgt_model_list = UpdateDataList(tgt_data_path, lyt_tgt_model_list)

    UpdateMaxBatchNum(len(src_data_list))


def UpdateDataList(data_path, lyt_data_list):
    load_data_names = LoadData(data_path)

    tmp_data_list = []
    lyt_data_list.RemoveAll()

    for i in range(len(load_data_names)):
        tmp_data = FBButton()
        tmp_data.Style = FBButtonStyle.kFBCheckbox
        tmp_data.Caption = load_data_names[i]
        tmp_data.Left = 5
        tmp_data.State = True
        lyt_data_list.Add(tmp_data, 20)
        tmp_data_list.append(tmp_data)
    
    return tmp_data_list


### UI Layout
def PopulateLayout(main_lyt):
    # Create a main layout
    x = FBAddRegionParam(10,FBAttachType.kFBAttachLeft,"")
    y = FBAddRegionParam(0,FBAttachType.kFBAttachTop,"")
    w = FBAddRegionParam(0,FBAttachType.kFBAttachRight,"")
    h = FBAddRegionParam(0,FBAttachType.kFBAttachBottom,"")
    main_lyt.AddRegion("main","main", x, y, w, h)
    overall_lyt = FBVBoxLayout()
    main_lyt.SetControl("main", overall_lyt)
    
    ## Data setting
    lyt_src = FBVBoxLayout()
    overall_lyt.Add(lyt_src, 265)

    src_label = FBLabel()
    src_label.Caption = "Data setting"
    lyt_src.Add(src_label, 30)

    # Source motion data folder search
    lyt_src_search = FBHBoxLayout()
    lyt_src.Add(lyt_src_search, 20)

    src_search_l = FBLabel()
    src_search_l.Caption = "Source motion data path: "
    lyt_src_search.Add(src_search_l, 145)

    src_search_e = FBEdit()
    src_search_e.Text = "D:/Research/CHOIR/01_data/SAMP/original"
    lyt_src_search.Add(src_search_e, 310)

    src_search_b = FBButton()
    src_search_b.Caption = "O"
    lyt_src_search.Add(src_search_b, 15)

    # Target character folder search
    lyt_tgt_search = FBHBoxLayout()
    lyt_src.Add(lyt_tgt_search, 20)

    tgt_search_l = FBLabel()
    tgt_search_l.Caption = "Target characters path: "
    lyt_tgt_search.Add(tgt_search_l, 145)

    tgt_search_e = FBEdit()
    tgt_search_e.Text = "D:/Research/CHOIR/01_data/SAMP/retarget/models"
    # tgt_search_e.Text = "D:/Research/CHOIR/01_data/SAMP/result/models"
    lyt_tgt_search.Add(tgt_search_e, 310)

    tgt_search_b = FBButton()
    tgt_search_b.Caption = "O"
    lyt_tgt_search.Add(tgt_search_b, 15)
    
    # Load data button
    load_data_b = FBButton()
    load_data_b.Caption = "Load Data"
    load_data_b.Look = FBButtonLook.kFBLookColorChange
    load_data_b.SetStateColor(FBButtonState.kFBButtonState0, FBColor(0.0, 0.0, 0.0))
    load_data_b.SetStateColor(FBButtonState.kFBButtonState1, FBColor(0.0, 0.3, 0.3))
    lyt_src.Add(load_data_b, 30)
    load_data_b.Width = lyt_src.Width - 10

    # Data list
    global src_data_list, tgt_model_list
    width = math.ceil((main_lyt.StartSizeX-20) / 2)
    lyt_show_data = FBHBoxLayout()
    lyt_src.Add(lyt_show_data, 150)
    
    # Source motion data list
    lyt_src_data = FBVBoxLayout()
    lyt_show_data.Add(lyt_src_data, width)

    
    src_data_names = LoadData(src_search_e.Text)
    src_data_list_l = FBLabel()
    src_data_list_l.Caption = "Source motion data list" \
                               + " (" + str(len(src_data_names)) + ")"
    lyt_src_data.Add(src_data_list_l, 20)

    src_data_list  = []
    lyt_src_data_list = FBVBoxLayout()
    for i in range(len(src_data_names)):
        tmp_data = FBButton()
        tmp_data.Style = FBButtonStyle.kFBCheckbox
        tmp_data.Caption = src_data_names[i]
        tmp_data.Left = 5
        tmp_data.State = True
        lyt_src_data_list.Add(tmp_data, 20)
        src_data_list.append(tmp_data)

    UpdateMaxBatchNum(len(src_data_list))    
    lyt_src_data.Add(lyt_src_data_list, 100)


    # Target character list
    lyt_tgt_model = FBVBoxLayout()
    lyt_show_data.Add(lyt_tgt_model, width)
    
    tgt_model_names = LoadData(tgt_search_e.Text)
    tgt_model_list_l = FBLabel()
    tgt_model_list_l.Caption = "Target character list" \
                                 + " (" + str(len(tgt_model_names)) + ")"
    lyt_tgt_model.Add(tgt_model_list_l, 20)

    tgt_model_list  = []
    lyt_tgt_model_list = FBVBoxLayout()
    for i in range(len(tgt_model_names)):
        tmp_model = FBButton()
        tmp_model.Style = FBButtonStyle.kFBCheckbox
        tmp_model.Caption = tgt_model_names[i]
        tmp_model.Left = 5
        tmp_model.State = True
        lyt_tgt_model_list.Add(tmp_model, 20)
        tgt_model_list.append(tmp_model)

    lyt_tgt_model.Add(lyt_tgt_model_list, 100)

    # add event to load data button    
    src_search_b.OnClick.Add(lambda control, event: OpenFolderExplorer(src_search_e, lyt_src_data_list, "source"))
    tgt_search_b.OnClick.Add(lambda control, event: OpenFolderExplorer(tgt_search_e, lyt_tgt_model_list, "target"))
    load_data_b.OnClick.Add(lambda control, event: UpdateSourceTargetList(src_search_e.Text, lyt_src_data_list,
                                                                          tgt_search_e.Text, lyt_tgt_model_list))


    ## Retargeting setting
    lyt_export = FBVBoxLayout()
    overall_lyt.Add(lyt_export, 300)

    retarget_label = FBLabel()
    retarget_label.Caption = "Export setting"
    lyt_export.Add(retarget_label, 30)
    
    # export path
    lyt_export_path = FBHBoxLayout()
    lyt_export.Add(lyt_export_path, 20)

    export_path_l = FBLabel()
    export_path_l.Caption = "Export path: "
    lyt_export_path.Add(export_path_l, 100)

    export_path_e = FBEdit()
    export_path_e.Text = tgt_search_e.Text.split("/models")[0]
    lyt_export_path.Add(export_path_e, 310)

    export_path_b = FBButton()
    export_path_b.Caption = "O"
    export_path_b.OnClick.Add(lambda control, event: OpenFolderExplorer(export_path_e))
    lyt_export_path.Add(export_path_b, 15)

    # export data type
    lyt_export_type = FBHBoxLayout()
    lyt_export.Add(lyt_export_type, 20)

    export_type_l = FBLabel()
    export_type_l.Caption = "Export data type: "
    lyt_export_type.Add(export_type_l, 100)

    export_type_c = FBList()
    export_type_c.Items.append("bvh")
    export_type_c.Items.append("fbx")
    lyt_export_type.Add(export_type_c, 100)

    # export fps
    lyt_export_fps = FBHBoxLayout()
    lyt_export.Add(lyt_export_fps, 20)
    
    export_fps_l = FBLabel()
    export_fps_l.Caption = "Export FPS: "
    lyt_export_fps.Add(export_fps_l, 100)

    export_fps_s = FBList()
    export_fps_s.Items.append("24")
    export_fps_s.Items.append("30")
    export_fps_s.Items.append("60")
    export_fps_s.Items.append("120")
    export_fps_s.ItemIndex = 2
    lyt_export_fps.Add(export_fps_s, 100)
    
    # batch size
    lyt_batch = FBHBoxLayout()
    lyt_export.Add(lyt_batch, 20)

    batch_l = FBLabel()
    batch_l.Caption = "Batch size: "
    lyt_batch.Add(batch_l, 100)

    batch_e = FBEditNumber()
    batch_e.Value = 1
    batch_e.OnChange.Add(lambda control, event: ClampValue(batch_e, 1, max_batch_num))
    lyt_batch.Add(batch_e, 100)


    # retargeting btn
    retarget_b = FBButton()
    retarget_b.Caption = "Retarget"
    retarget_b.Look = FBButtonLook.kFBLookColorChange
    retarget_b.SetStateColor(FBButtonState.kFBButtonState0, FBColor(0.0, 0.0, 0.0))
    retarget_b.SetStateColor(FBButtonState.kFBButtonState1, FBColor(0.0, 0.3, 0.3))
    retarget_b.OnClick.Add(lambda control, event: mbr.do_retarget(src_search_e.Text,
                                                                  GetSelectedDataNames(src_data_list),
                                                                  tgt_search_e.Text,
                                                                  GetSelectedDataNames(tgt_model_list),
                                                                  export_path_e.Text,
                                                                  export_type_c.Items[export_type_c.ItemIndex],
                                                                  export_fps_s.Items[export_fps_s.ItemIndex],
                                                                  int(batch_e.Value),
                                                                  False))
    lyt_export.Add(retarget_b, 30)
    retarget_b.Width = lyt_export.Width - 10


 
def CreateUI():    
    ui = FBCreateUniqueTool("Retargeting")
    ui.StartSizeX = 515
    ui.StartSizeY = 500
    ui.StartPosX  = 1400
    ui.StartPosY  = 200
    ui.OnUnbind.Add(OnUnbind)

    PopulateLayout(ui)
    ShowTool(ui)

    # FBDestroyTool(t)


CreateUI()
