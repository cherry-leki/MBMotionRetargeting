import os
from joint_dict import MB_JOINTS, MB_SMPL_JOINTS
from export_bvh import export_bvh

from pyfbsdk import *

# to install numpy for motionbuilder, please refer to: https://help.autodesk.com/view/MOBPRO/2022/ENU/?guid=GUID-46E090C5-34AD-4E26-872F-F7D21DC57C74

# Tutorials/code I referred to:
# https://help.autodesk.com/view/MOBPRO/2019/ENU/?guid=__files_GUID_A1189AA0_3816_4350_B8F3_5383DEC25A33_htm
# https://github.com/eksod/Retargeter


""" ======================================================  Mobupy Functions  ======================================================  """
""" create skeleton, characterize, plot animation, switch take, etc                 """
def deselect_all():
    modelList = FBModelList()
    FBGetSelectedModels(modelList, None, True)
    for model in modelList:
        model.Selected = False

def recursive_select(node, types=None):
    if (not types or isinstance(node, types)) and not node.Selected:
        node.Selected = True
    for child in node.Children:
        recursive_select(child)

def check_model_is_SMPL(hip):
    ck_hip_name = False
    ck_left_hip = False
    ck_left_collar = False

    # check hip joint
    if "pelvis" in hip.LongName.lower():
        ck_hip_name = True

    left_hip = None
    spine = None
    for child in hip.Children:
        if "left" in child.LongName.lower():
            left_hip = child
        if "spine" in child.LongName.lower():
            spine = child

    # check left hip joint
    if left_hip and "left_hip" in left_hip.LongName.lower():
        ck_left_hip = True

    # check left collar joint
    while spine != None:
        if len(spine.Children) > 1:
            for child in spine.Children:
                if "left_collar" in child.LongName.lower():
                    ck_left_collar = True
                    break
            break

        if "spine" in spine.LongName.lower():
            spine = spine.Children[0]
            continue            

    return ck_hip_name and ck_left_hip and ck_left_collar

# recursive function to add namespace to all children of a joint
def add_namespace(joint, namespace):
    joint.LongName = f"{namespace}:{joint.Name}"
    for child in joint.Children:
        add_namespace(child, namespace)

def remove_namespace(joint, namespace):
    joint.LongName = joint.LongName.replace(f"{namespace}:", "")
    for child in joint.Children:
        remove_namespace(child, namespace)


""" [TODO]
If bvh skeleton contains joints that are not in the MotionBuilder's biped character map,
append the bvh joint name to `joint_candidates[mobu joint name]` list.

# joint_candidates: A dictionary mapping mobu joints to bvh joints (all candidates)
#     - key: mobu Joint Names
#     - value: [bvhJointName...] candidate List
"""
def CharacterizeBiped(namespace, hip):
    myBiped = FBCharacter(f"{namespace}: mycharacter")
    myBiped.LongName = f"{namespace}: mycharacter"
    FBApplication().CurrentCharacter = myBiped

    # choose joint dict
    joint_candidates = {"LeftToeBase": ["LeftToe"], "RightToeBase": ["RightToe"]}
    if check_model_is_SMPL(hip):
        joint_candidates = MB_SMPL_JOINTS

    # assign Biped to Character Mapping.
    for mobuJoint in MB_JOINTS:
        modelLongName = f"{namespace}:{mobuJoint}" if namespace else mobuJoint
        myJoint = FBFindModelByLabelName(modelLongName)
        if (not myJoint) and (mobuJoint in joint_candidates):
            for bvh_joint_candidate in joint_candidates[mobuJoint]:
                modelLongName = (
                    f"{namespace}:{bvh_joint_candidate}"
                    if namespace
                    else bvh_joint_candidate
                )
                myJoint = FBFindModelByLabelName(modelLongName)
                if myJoint:
                    break
        # print(modelLongName, myJoint)
        if myJoint:
            proplist = myBiped.PropertyList.Find(mobuJoint + "Link")
            proplist.append(myJoint)

    switchOn = myBiped.SetCharacterizeOn(True)
    # print "Character mapping created for " + (myBiped.LongName)

    return myBiped


def plotAnim(char, animChar):
    """
    Receives two characters, sets the input of the first character to the second
    and plot. Return ploted character.
    """
    # if char.GetCharacterize:
    #    switchOn = char.SetCharacterizeOn(True)

    plotoBla = FBPlotOptions()
    plotoBla.ConstantKeyReducerKeepOneKey = True
    plotoBla.PlotAllTakes = False
    plotoBla.PlotOnFrame = True
    plotoBla.PlotPeriod = FBTime(0, 0, 0, 1)
    plotoBla.PlotTranslationOnRootOnly = True
    plotoBla.PreciseTimeDiscontinuities = True
    # plotoBla.RotationFilterToApply = FBRotationFilter.kFBRotationFilterGimbleKiller
    plotoBla.UseConstantKeyReducer = False
    plotoBla.ConstantKeyReducerKeepOneKey = True
    char.InputCharacter = animChar
    char.InputType = FBCharacterInputType.kFBCharacterInputCharacter
    char.ActiveInput = True
    if not char.PlotAnimation(
        FBCharacterPlotWhere.kFBCharacterPlotOnSkeleton, plotoBla
    ):
        FBMessageBox(
            "Something went wrong",
            "Plot animation returned false, cannot continue",
            "OK",
            None,
            None,
        )
        return False

    return char


def SwitchTake(pTakeName):
    iDestName = pTakeName
    for iTake in FBSystem().Scene.Takes:
        if iTake.Name == iDestName:
            FBSystem().CurrentTake = iTake


def skelExists(root, name):
    if root == None:
        return False
    if root.Name == name:
        return True
    for child in root.Children:
        if skelExists(child, name):
            return True
    return False

def select_branch(model):
    for child in model.Children:
        select_branch(child)
    
    model.Selected = True


""" ======================================================  MAIN  ======================================================  """
def do_retarget(src_data_path, src_data_list,
                tgt_model_path, tgt_model_list,
                export_path, export_type, export_fps,
                batch_size, merge_skel):
    print("Start Retargeting...")

    # check export path
    if not os.path.exists(export_path):
        print(f"Export path does not exist: {export_path}")
        return
    # append results to the export path
    export_path = os.path.join(export_path, "results")

    # source motion files
    src_motion_files = []
    for si in range(len(src_data_list)):
        tmp_path = os.path.join(src_data_path, src_data_list[si] + ".bvh")
        if os.path.exists(tmp_path):
            src_motion_files.append(tmp_path)
            continue

        tmp_path = tmp_path.replace(".bvh", ".fbx")
        if os.path.exists(tmp_path):
            src_motion_files.append(tmp_path)
            continue

    # target character models
    tgt_character_files = []
    for ti in range(len(tgt_model_list)):
        tmp_path = os.path.join(tgt_model_path, tgt_model_list[ti] + ".fbx")
        if os.path.exists(tmp_path):
            tgt_character_files.append(tmp_path)
        save_path = os.path.join(export_path, tgt_model_list[ti])
        if not os.path.exists(save_path):
            os.makedirs(save_path)

    if len(src_motion_files) == 0:
        print("No source motion files found.")
        return
    
    if len(tgt_character_files) == 0:
        print("No target character files found.")
        return

    # fps setting
    fps = FBTimeMode.kFBTimeMode60Frames
    if export_fps == "24":
        fps = FBTimeMode.kFBTimeMode24Frames
    elif export_fps == "30":
        fps = FBTimeMode.kFBTimeMode30Frames
    elif export_fps == "60":
        fps = FBTimeMode.kFBTimeMode60Frames
    elif export_fps == "120":
        fps = FBTimeMode.kFBTimeMode120Frames


    # initialize
    system = FBSystem()
    scene  = system.Scene
    app    = FBApplication()
    player = FBPlayerControl()    

    # batch setting
    total = len(src_data_list)
    batches = list(range(0, total, batch_size))
    if batches[-1] == total:
        batches = batches[:-1]
    batches.append(total + 1)

    # retargeting
    for bi in range(len(batches)-1):
        app.FileNew()
        val_char_list = []
        val_mo_file_list = []
        valid_m_num = 0

        cnt_modelskel = 0
        src_prefix = None
        # load motion files
        for mi, mo_file in enumerate(src_motion_files[batches[bi]:batches[bi+1]]):
            cnt_modelskel = len(scene.ModelSkeletons)
            mo_file_name = mo_file.split(os.sep)[-1].split(".")[0]

            # new_take = FBTake(mo_file_name)
            # system.Scene.Takes.append(new_take)
            # SwitchTake(mo_file_name)
            # new_take.ClearAllProperties(False)
            success = app.FileImport(mo_file, merge_skel)
            if not success:
                print(f"Failed to load {mo_file}")
                exit()
            new_take = system.Scene.Takes[-1]
            new_take.LongName = mo_file_name
            SwitchTake(mo_file_name)

            valid_m_num += 1

            # set frame rate
            FBPlayerControl().SetTransportFps(fps)
            if merge_skel:
                src_prefix = None
            elif mo_file.endswith(".fbx"):
                src_prefix = "FBX" if mi == 0 else "FBX " + str(mi)
                root = scene.ModelSkeletons[cnt_modelskel]
                add_namespace(root, src_prefix)

                if root.Parent:
                    root.Parent.LongName = f"{src_prefix}:{root.Parent.LongName}"
            else:
                src_prefix = "BVH" if mi == 0 else "BVH " + str(mi)
                reference_long_name = src_prefix + ":reference"
                if FBFindModelByLabelName(reference_long_name):
                    FBFindModelByLabelName(reference_long_name).FBDelete()
            
            # characterize source motion's skeleton
            if (not merge_skel) or (mi == 0):
                # make t-pose
                hip = None
                hip_names = ["hip", "pelvis"]
                check_hip = False
                for joint in scene.ModelSkeletons[cnt_modelskel:]:
                    if src_prefix not in joint.LongName: continue
                    joint.Rotation = FBVector3d(0, 0, 0)    # zero-rotation

                    if not check_hip:
                        if any([h in joint.LongName.lower() for h in hip_names]):
                            hip = joint
                            joint.Translation = FBVector3d(0, joint.Translation[1], 0)  # zero-translation xz
                            check_hip = True

                scene.Evaluate()

                # move hips so that foot touches the ground
                left_leg = [joint for joint in hip.Children if "left" in joint.LongName.lower()][0] 
                ee_height = 0
                while left_leg != None:
                    j_pos = FBVector3d()
                    left_leg.GetVector(j_pos, FBModelTransformationType.kModelTranslation, True)
                    if j_pos[1] > ee_height:
                        break                        
                    else:
                        ee_height = -j_pos[1]

                        if left_leg.Children == None:
                            break
                        left_leg = left_leg.Children[0]
                hip.Translation = FBVector3d(hip.Translation[0], hip.Translation[1] + ee_height, hip.Translation[2])
                scene.Evaluate()

                # characterize biped
                anim_char = CharacterizeBiped(src_prefix, hip)
                anim_char.SelectModels(True, True, True, False)
                player = FBPlayerControl()
                player.Goto(FBTime(0, 0, 0, 0))
                val_char_list.append(anim_char)

                cnt_modelskel = len(scene.ModelSkeletons)
            
            # set time span
            l_end_frame = system.CurrentTake.LocalTimeSpan.GetStop().GetFrame()
            l_start_frame = system.CurrentTake.LocalTimeSpan.GetStart().GetFrame()
            val_mo_file_list.append([mo_file_name, l_start_frame, l_end_frame])
            deselect_all()

        for comp in scene.Components:
            comp.Selected = False
        

        # load target character files
        for ci, char_file in enumerate(tgt_character_files):
            cnt_modelskel = len(scene.ModelSkeletons)
            # merge fbx target model
            m_options = FBFbxOptions(True)  # true = load options
            for m_take_index in range(m_options.GetTakeCount()):
                m_options.SetTakeSelect(m_take_index, False)
            m_options.Character = FBElementAction.kFBElementActionDiscard
            m_options.CamerasAnimation = False
            app.FileMerge(char_file, False, m_options)

            hip = None
            hip_names = ["hip", "pelvis"]
            for joint in scene.ModelSkeletons[cnt_modelskel:]:
                if any([h in joint.LongName.lower() for h in hip_names]):
                    hip = joint
                    break

            prefix = ""
            if ":" not in hip.LongName:
                prefix = "target" + str(ci)
                add_namespace(hip, prefix)                
            else:
                prefix = hip.LongName.split(":")[0]

            character = CharacterizeBiped(prefix, hip)
            character.SelectModels(True, True, True, False)
            
            pose_options = FBCharacterPoseOptions()
            pose_options.mCharacterPoseKeyingMode = (
                FBCharacterPoseKeyingMode.kFBCharacterPoseKeyingModeFullBody
            )

            # retargeting
            for vm_i in range(valid_m_num):
                SwitchTake(val_mo_file_list[vm_i][0])
                FBPlayerControl().SetTransportFps(fps)

                system.CurrentTake.LocalTimeSpan = FBTimeSpan(
                    FBTime(0, 0, 0, val_mo_file_list[vm_i][1]),
                    FBTime(0, 0, 0, val_mo_file_list[vm_i][2]),
                )

                # key all frames for bvh to prevent unwanted interpolation between frames
                l_end_time = system.CurrentTake.LocalTimeSpan.GetStop()
                l_end_frame = system.CurrentTake.LocalTimeSpan.GetStop().GetFrame()
                l_start_frame_time = system.CurrentTake.LocalTimeSpan.GetStart()
                l_start_frame = system.CurrentTake.LocalTimeSpan.GetStart().GetFrame()

                l_range = int(l_end_frame) + 1

                for i in range(l_range):
                    player.Goto(FBTime(0, 0, 0, i))
                    scene.Evaluate()
                    player.Key()
                    scene.Evaluate()              

                player.Goto(FBTime(0, 0, 0, 0))
                anim_char = val_char_list[0] if merge_skel else val_char_list[vm_i]
                plotAnim(character, anim_char)
                character.SelectModels(True, True, True, True)
                
                # remove namespace if not exist in the original name
                if "target" in prefix:
                    remove_namespace(hip, prefix)

                # save in file
                # recursive_select(hip, FBModelSkeleton)

                save_options = FBFbxOptions(False)
                save_options.SaveCharacter = False
                save_options.SaveSelectedModelsOnly = True
                save_options.SaveControlSet = False
                save_options.SaveCharacterExtensions = False
                save_options.ShowFileDialog = False
                save_options.ShowOptionsDialog = False

                mo_name   = val_mo_file_list[vm_i][0]
                char_name = tgt_model_list[ci]
                save_path = os.path.join(export_path, char_name,
                                         char_name + "_" + mo_name + f".{export_type}")
                if export_type == "fbx":
                    app.FileExport(save_path)
                if export_type == "bvh":
                    app.FileExport(save_path)
                    # export_bvh(hip, save_path, float(export_fps))
                print(f"Exported: {save_path}")

            character.FBDelete()

            # delete all models except for source models
            for model in scene.RootModel.Children:
                if src_prefix not in model.LongName:
                    select_branch(model)

            selected_models = FBModelList()
            FBGetSelectedModels(selected_models, None, True)
            for model in selected_models:
                model.FBDelete()
            
            deselect_all()
            for comp in scene.Components:
                comp.Selected = False
                