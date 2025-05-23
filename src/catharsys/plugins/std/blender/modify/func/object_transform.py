#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# File: \data\obj_modify.py
# Created Date: Friday, August 13th 2021, 8:12:19 am
# Author: Christian Perwass (CR/AEC5)
# <LICENSE id="GPL-3.0">
#
#   Image-Render standard Blender actions module
#   Copyright (C) 2022 Robert Bosch GmbH and its subsidiaries
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#
# </LICENSE>
###

import bpy
import mathutils

import math
from anyblend import object as anyobj
from anyblend import ops_object as anyops
from anyblend import viewlayer as anyvl

from anycam import ops as camops

# from anybase import convert, config
# from anybase.cls_any_error import CAnyError_Message
from anybase.dec.cls_paramclass import paramclass, CParamFields


from catharsys.decs.decorator_ep import EntryPoint
from catharsys.util.cls_entrypoint_information import CEntrypointInformation


############################################################################################


@paramclass
class CSetOriginParams:
    sDTI: str = (
        CParamFields.HINT(sHint="entry point identification"),
        CParamFields.REQUIRED("blender/modify/object/set-origin:1.0"),
    )
    # sMode: str = CParamFields.OPTIONS(["INIT", "FRAME_UPDATE"], xDefault="INIT")
    sOriginType: str = CParamFields.OPTIONS(
        ["GEOMETRY_ORIGIN", "ORIGIN_GEOMETRY", "ORIGIN_CURSOR", "ORIGIN_CENTER_OF_MASS", "ORIGIN_CENTER_OF_VOLUME"],
        xDefault="GEOMETRY_ORIGIN",
    )
    sCenter: str = CParamFields.OPTIONS(["MEDIAN", "BOUNDS"], xDefault="MEDIAN")


# endclass


# -------------------------------------------------------------------------------------------
@EntryPoint(
    CEntrypointInformation.EEntryType.MODIFIER,
    clsInterfaceDoc=CSetOriginParams,
)
def SetOrigin(_objX, _dicMod, **kwargs):
    # -- from dict to paramclass
    # -- assertions on OPTIONS are be done inside paramclass
    paramMod = CSetOriginParams(_dicMod)

    anyops.SetOriginByType(_objX, _sOriginType=paramMod.sOriginType, _sCenter=paramMod.sCenter)
    anyvl.Update()

    return None


# enddef


############################################################################################


@paramclass
class CDeltaRotationEulerParams:
    sDTI: str = (
        CParamFields.HINT(sHint="entry point identification"),
        CParamFields.REQUIRED("blender/modify/object/delta-rotation-euler:1.1"),
        CParamFields.DEPRECATED("sType"),
    )
    sMode: str = CParamFields.OPTIONS(["INIT", "FRAME_UPDATE"], xDefault="INIT")
    sUnit: str = CParamFields.OPTIONS(["deg", "rad"], xDefault="rad")
    sFrame: str = CParamFields.OPTIONS(["world", "local"], xDefault="local")
    lValue: list = (CParamFields.REQUIRED(list[float, float, float]), CParamFields.DEPRECATED("xValue"))

    def __post_init__(self, _dictArgs):
        if self.sUnit == "deg":
            self.lValue = [math.radians(x) for x in self.lValue]
        # endif -- conversion to radians

    # end def

    def getMatrixWorld(self, _objX):
        matObj = _objX.matrix_world
        matRot = mathutils.Euler(tuple(self.lValue)).to_matrix().to_4x4()

        # print("location: {}".format(_objX.location))
        # print("matObj:\n{}".format(convert.MatrixToString(matObj)))
        # print("matRot:\n{}".format(convert.MatrixToString(matRot)))

        if self.sFrame.lower() == "local":
            matWorld = matObj @ matRot
        else:
            matWorld = matRot @ matObj
        # endif

        return matWorld

    # end def


# endclass


# -------------------------------------------------------------------------------------------
@EntryPoint(
    CEntrypointInformation.EEntryType.MODIFIER,
    clsInterfaceDoc=CDeltaRotationEulerParams,
)
def DeltaRotationEuler(_objX, _dicMod, **kwargs):
    """
    rotates an object arround a given axis with given angle
    """

    # -- from dict to paramclass
    # -- assertions on OPTIONS are be done inside paramclass
    paramMod = CDeltaRotationEulerParams(_dicMod)

    if _objX.type == "CAMERA":
        objX = camops.GetAnyCamTopObject(_objX.name)
    else:
        objX = _objX
    # endif

    # Set delta rotation of object as a delta to the current rotation
    # Store in the rotation and not delta_rotation, as animations are
    # applied to delta rotation variable.
    objX.matrix_world = paramMod.getMatrixWorld(_objX)

    anyvl.Update()


# enddef


############################################################################################
############################################################################################
@paramclass
class CRotationEulerParams:
    sDTI: str = (
        CParamFields.HINT(sHint="entry point identification"),
        CParamFields.REQUIRED("blender/modify/object/rotation-euler:1.1"),
        CParamFields.DEPRECATED("sType"),
    )
    sUnit: str = CParamFields.OPTIONS(["deg", "rad"], xDefault="rad")

    lRotAngles: list = (CParamFields.REQUIRED(list[float, float, float]), CParamFields.DEPRECATED("xValue"))

    def __post_init__(self, _dictArgs):
        if self.sUnit == "deg":
            self.lRotAngles = [math.radians(x) for x in self.lRotAngles]
        # endif -- conversion to radians

    # end def


# endclass


# -------------------------------------------------------------------------------------------
@EntryPoint(
    CEntrypointInformation.EEntryType.MODIFIER,
    clsInterfaceDoc=CRotationEulerParams,
)
def RotationEuler(_objX, _dicMod, **kwargs):
    """
    sets the rotation fot the given object with given angle
    """

    # print(f"Rotation-Euler: {_dicMod}")

    # -- from dict to paramclass
    # -- assertions on OPTIONS are be done inside paramclass
    paramMod = CRotationEulerParams(_dicMod)

    if _objX.type == "CAMERA":
        objX = camops.GetAnyCamTopObject(_objX.name)
    else:
        objX = _objX
    # endif

    objX.rotation_euler = mathutils.Euler(mathutils.Vector(paramMod.lRotAngles))
    anyvl.Update()


# enddef


############################################################################################
def _Metric2BlenderScale(_sUnit: str):
    dMeterPerUnit = 1.0
    if _sUnit == "m":
        dMeterPerUnit = 1.0
    elif _sUnit == "mm":
        dMeterPerUnit = 1e-3
    elif _sUnit == "um":
        dMeterPerUnit = 1e-6
    elif _sUnit == "km":
        dMeterPerUnit = 1e3
    else:
        raise Exception("Unkown unit '{0}'.".format(_sUnit))
    # endif

    dScale = dMeterPerUnit / bpy.context.scene.unit_settings.scale_length
    return dScale


# enddef


############################################################################################
############################################################################################
@paramclass
class CDeltaLocationParams:
    sDTI: str = (
        CParamFields.HINT(sHint="entry point identification"),
        CParamFields.REQUIRED("blender/modify/object/delta-location:1.1"),
        CParamFields.DEPRECATED("sType"),
    )
    sMode: str = CParamFields.OPTIONS(["INIT", "FRAME_UPDATE"], xDefault="INIT")

    sUnit: str = CParamFields.OPTIONS(["m", "mm", "um", "km"], xDefault="mm")
    lLoc: list = (CParamFields.REQUIRED(list[float, float, float]), CParamFields.DEPRECATED("xValue"))


# endclass


# -------------------------------------------------------------------------------------------
@EntryPoint(
    CEntrypointInformation.EEntryType.MODIFIER,
    clsInterfaceDoc=CDeltaLocationParams,
)
def DeltaLocation(_objX, _dicMod, **kwargs):
    """
    adds a distance vector to an object
    """

    paramMod = CDeltaLocationParams(_dicMod)

    # Set delta location of object
    dScale = _Metric2BlenderScale(paramMod.sUnit)
    lLoc_bu = [dScale * x for x in paramMod.lLoc]

    if _objX.type == "CAMERA":
        objX = camops.GetAnyCamTopObject(_objX.name)
    else:
        objX = _objX
    # endif

    objX.location += mathutils.Vector(lLoc_bu)
    anyvl.Update()


# enddef


############################################################################################
############################################################################################
@paramclass
class CDeltaTransformProxyParams:
    sDTI: str = (
        CParamFields.HINT(sHint="entry point identification"),
        CParamFields.REQUIRED("blender/modify/object/delta-transform/proxy:1.0"),
        CParamFields.DEPRECATED("sType"),
    )

    sFrom: str = (
        CParamFields.REQUIRED(str),
        CParamFields.HINT("name of the proxy object that is used as reference as transform starting point"),
    )

    sTo: str = (
        CParamFields.REQUIRED(str),
        CParamFields.HINT("name of the proxy object that is used as reference as transform end point"),
    )

    # fFactor: float = (
    #     CParamFields.DEFAULT(1.0),
    #     CParamFields.DISPLAY("factor for the transformation"),
    #     CParamFields.HINT("factor for the transformation"),
    # )

    # bUseScale: bool = (
    #     CParamFields.DEFAULT(False),
    #     CParamFields.DISPLAY("use scale"),
    #     CParamFields.HINT("use scale of the proxy objects"),
    # )

    # bUseRotation: bool = (
    #     CParamFields.DEFAULT(True),
    #     CParamFields.DISPLAY("use rotation"),
    #     CParamFields.HINT("use rotation of the proxy objects"),
    # )

    # bUseTranslation: bool = (
    #     CParamFields.DEFAULT(True),
    #     CParamFields.DISPLAY("use translation"),
    #     CParamFields.HINT("use translation of the proxy objects"),
    # )

    # bLocalFrame: bool = (
    #     CParamFields.DEFAULT(False),
    #     CParamFields.DISPLAY("use local frame"),
    #     CParamFields.HINT("use local frame of the proxy objects"),
    # )

    sMode: str = CParamFields.OPTIONS(["INIT", "FRAME_UPDATE"], xDefault="INIT")


# endclass


# -------------------------------------------------------------------------------------------
@EntryPoint(
    CEntrypointInformation.EEntryType.MODIFIER,
    clsInterfaceDoc=CDeltaTransformProxyParams,
)
def DeltaTransformProxy(_objX, _dicMod, **kwargs):
    """
    Transform an object by the difference in pose of two other proxy objects.
    For example, if the proxy objects are two empties, the object will be transformed
    by the difference in pose of the two empties.
    This is useful for creating complex animations where the object needs to follow
    the difference in pose of two other objects.
    """

    paramMod = CDeltaTransformProxyParams(_dicMod)

    if _objX.type == "CAMERA":
        objX = camops.GetAnyCamTopObject(_objX.name)
    else:
        objX = _objX
    # endif

    objFrom = bpy.data.objects.get(paramMod.sFrom)
    if objFrom is None:
        raise RuntimeError(f"Proxy 'from' object '{paramMod.sFrom}' not found")
    # endif

    objTo = bpy.data.objects.get(paramMod.sTo)
    if objTo is None:
        raise RuntimeError(f"Proxy 'to' object '{paramMod.sTo}' not found")
    # endif

    # if paramMod.fFactor == 0.0:
    #     return
    # # endif

    # if paramMod.fFactor < 0.0:
    #     temp = objFrom
    #     objFrom = objTo
    #     objTo = temp
    #     paramMod.fFactor = -paramMod.fFactor
    # # endif

    # iCount = math.floor(paramMod.fFactor)
    # fFactor = paramMod.fFactor - iCount

    # matDiff = objTo.matrix_world @ objFrom.matrix_world.inverted()
    # objX.matrix_world = matDiff @ objX.matrix_world

    vOTrans, qORot, vOScale = objX.matrix_world.decompose()
    vFTrans, qFRot, vFScale = objFrom.matrix_world.decompose()
    vTTrans, qTRot, vTScale = objTo.matrix_world.decompose()

    print(f"vOTrans: {vOTrans}, qORot: {qORot}, vOScale: {vOScale}")
    print(f"vFTrans: {vFTrans}, qFRot: {qFRot}, vFScale: {vFScale}")
    print(f"vTTrans: {vTTrans}, qTRot: {qTRot}, vTScale: {vTScale}")

    diffTrans = vTTrans - vFTrans
    diffRot = qFRot.rotation_difference(qTRot)
    vScale = mathutils.Vector((1.0, 1.0, 1.0))
    print(f"diffTrans: {diffTrans}, diffRot: {diffRot}, vScale: {vScale}")

    matObject = mathutils.Matrix.LocRotScale(vOTrans, qORot, vScale)
    print(f"matObject:\n{matObject}")

    matFrom = mathutils.Matrix.LocRotScale(vFTrans, qFRot, vScale)
    print(f"matFrom:\n{matFrom}")

    matTransform = mathutils.Matrix.LocRotScale(diffTrans, diffRot, vScale)
    print(f"matTransform:\n{matTransform}")

    # objX.matrix_world = matFrom @ matTransform @ matFrom.inverted() @ matObject.inverted() @ objX.matrix_world 
    # objX.matrix_world = mathutils.Matrix.Translation(diffTrans).to_4x4() @ matObject.inverted() @ objX.matrix_world 

    # objX.matrix_world = matObject @ diffRot.to_matrix().to_4x4() @ mathutils.Matrix.Translation(diffTrans).to_4x4() @ matObject.inverted() @ objX.matrix_world 
    objX.matrix_world = matObject @ matTransform @ matObject.inverted() @ objX.matrix_world 

    # objX.matrix_world = matObject @ matFrom @ matTransform @ matFrom.inverted() @ matObject.inverted() @ objX.matrix_world 

    # if fFactor > 1e-6:
    #     qPartRot = qFRot.slerp(qTRot, fFactor)
    #     diffPartRot = qFRot.rotation_difference(qPartRot)
    # else:
    #     diffPartRot = None
    # # endif 

    # diffScale = vTScale
    # diffScale[0] /= vFScale[0]
    # diffScale[1] /= vFScale[1]
    # diffScale[2] /= vFScale[2]
    # diffScale *= paramMod.fFactor
    
    # matTrans = mathutils.Matrix.Identity(4)
    # matTransInv = mathutils.Matrix.Identity(4)
    # matRot = mathutils.Matrix.Identity(4)
    # matScale = mathutils.Matrix.Identity(4)

    # if paramMod.bUseTranslation:
    #     # if paramMod.bLocalFrame: 
    #     #     diffTrans = -diffTrans
    #     matTrans = mathutils.Matrix.Translation(diffTrans)
    #     matTransInv = mathutils.Matrix.Translation(-diffTrans)

    # if paramMod.bUseRotation:
    #     for i in range(iCount):
    #         matRot @= diffRot.to_matrix().to_4x4()
    #     if diffPartRot is not None:
    #         matRot @= diffPartRot.to_matrix().to_4x4()

    # if paramMod.bUseScale:
    #     matScale = mathutils.Matrix.Diagonal(diffScale).to_4x4()

    # if paramMod.bLocalFrame:
    #     objX.matrix_world = objTo.matrix_world @ objFrom.matrix_world.inverted() @ objX.matrix_world
    #     # vTrans, qRot, vScale = objX.matrix_world.decompose()
    #     # matTrans = mathutils.Matrix.Translation(vTrans) @ matTrans
    #     # matRot = qRot.to_matrix().to_4x4() @ matRot
    #     # matScale = mathutils.Matrix.Diagonal(vScale).to_4x4() @ matScale
    #     # objX.matrix_world = matTrans @ matRot @ matScale
    # else:
    #     objX.matrix_world = matTrans @ matRot @ matScale @ objX.matrix_world
    # # endif
    
    anyvl.Update()


# enddef

############################################################################################
############################################################################################
@paramclass
class CMoveToParams:
    sDTI: str = (
        CParamFields.HINT(sHint="entry point identification"),
        CParamFields.REQUIRED("blender/modify/object/move/to:1.0"),
        CParamFields.DEPRECATED("sType"),
    )

    sTarget: str = (
        CParamFields.REQUIRED(str),
        CParamFields.HINT("name of the target object where this object is moved to"),
    )

    sMode: str = CParamFields.OPTIONS(["INIT", "FRAME_UPDATE"], xDefault="INIT")


# endclass


# -------------------------------------------------------------------------------------------
@EntryPoint(
    CEntrypointInformation.EEntryType.MODIFIER,
    clsInterfaceDoc=CMoveToParams,
)
def MoveTo(_objX, _dicMod, **kwargs):
    """
    Move an object to the position and orientation of a target object.
    This is like parenting but without the parent-child relationship.
    """

    paramMod = CMoveToParams(_dicMod)

    if _objX.type == "CAMERA":
        objX = camops.GetAnyCamTopObject(_objX.name)
    else:
        objX = _objX
    # endif

    objTarget = bpy.data.objects.get(paramMod.sTarget)
    if objTarget is None:
        raise RuntimeError(f"Target object '{paramMod.sTarget}' not found")
    # endif

    vOTrans, qORot, vOScale = objX.matrix_world.decompose()
    vTTrans, qTRot, vTScale = objTarget.matrix_world.decompose()
    vScale = mathutils.Vector((1.0, 1.0, 1.0))

    matTarget = mathutils.Matrix.LocRotScale(vTTrans, qTRot, vScale)
    matObject = mathutils.Matrix.LocRotScale(vOTrans, qORot, vScale)
 
    objX.matrix_world = matTarget @ matObject.inverted() @ mathutils.Matrix.Diagonal(vOScale).to_4x4()

    
    anyvl.Update()


# enddef

############################################################################################
############################################################################################
@paramclass
class CMoveFromParams:
    sDTI: str = (
        CParamFields.HINT(sHint="entry point identification"),
        CParamFields.REQUIRED("blender/modify/object/move/from:1.0"),
        CParamFields.DEPRECATED("sType"),
    )

    sTarget: str = (
        CParamFields.REQUIRED(str),
        CParamFields.HINT("name of the target object which will lie at this object's current position after transformation"),
    )

    sMode: str = CParamFields.OPTIONS(["INIT", "FRAME_UPDATE"], xDefault="INIT")


# endclass


# -------------------------------------------------------------------------------------------
@EntryPoint(
    CEntrypointInformation.EEntryType.MODIFIER,
    clsInterfaceDoc=CMoveFromParams,
)
def MoveFrom(_objX, _dicMod, **kwargs):
    """
    Move an object to the position and orientation of a target object.
    This is like parenting but without the parent-child relationship.
    """

    paramMod = CMoveFromParams(_dicMod)

    if _objX.type == "CAMERA":
        objX = camops.GetAnyCamTopObject(_objX.name)
    else:
        objX = _objX
    # endif

    objTarget = bpy.data.objects.get(paramMod.sTarget)
    if objTarget is None:
        raise RuntimeError(f"Target object '{paramMod.sTarget}' not found")
    # endif

    vOTrans, qORot, vOScale = objX.matrix_world.decompose()
    vTTrans, qTRot, vTScale = objTarget.matrix_world.decompose()

    vScale = mathutils.Vector((1.0, 1.0, 1.0))
    matObject = mathutils.Matrix.LocRotScale(vOTrans, qORot, vScale)
    matTarget = mathutils.Matrix.LocRotScale(vTTrans, qTRot, vScale)

    # matDiff = matObject.inverted() @ matTarget
    matDiff = matTarget.inverted() @ matObject
    vTrans, qRot, vScale = matDiff.decompose()

    print(f"vOTrans: {vOTrans}, qORot: {qORot}, vOScale: {vOScale}")
    print(f"vTTrans: {vTTrans}, qTRot: {qTRot}, vTScale: {vTScale}")

    objX.matrix_world = matObject @ matTarget.inverted() @ objX.matrix_world
    
    anyvl.Update()


# enddef

############################################################################################
############################################################################################
@paramclass
class CLocationParams:
    sDTI: str = (
        CParamFields.HINT(sHint="entry point identification"),
        CParamFields.REQUIRED("blender/modify/object/location:1.1"),
        CParamFields.DEPRECATED("sType"),
    )

    sUnit: str = CParamFields.OPTIONS(["m", "mm", "um", "km"], xDefault="mm")
    lLoc: list = (CParamFields.REQUIRED(list[float, float, float]), CParamFields.DEPRECATED("xValue"))


# endclass


# -------------------------------------------------------------------------------------------
@EntryPoint(
    CEntrypointInformation.EEntryType.MODIFIER,
    clsInterfaceDoc=CLocationParams,
)
def Location(_objX, _dicMod, **kwargs):
    """
    sets the location of an object
    """

    paramMod = CLocationParams(_dicMod)

    # Set delta location of object
    dScale = _Metric2BlenderScale(paramMod.sUnit)
    lLoc_bu = [dScale * x for x in paramMod.lLoc]

    if _objX.type == "CAMERA":
        objX = camops.GetAnyCamTopObject(_objX.name)
    else:
        objX = _objX
    # endif

    objX.location = mathutils.Vector(lLoc_bu)
    anyvl.Update()


# enddef


############################################################################################
############################################################################################
@paramclass
class CScaleParams:
    sDTI: str = (
        CParamFields.HINT(sHint="entry point identification"),
        CParamFields.REQUIRED("blender/modify/object/scale:1.1"),
        CParamFields.DEPRECATED("sType"),
    )

    lScale: list = (
        CParamFields.REQUIRED(list[float, float, float]),
        CParamFields.DEPRECATED("xValue"),
        CParamFields.HINT("scale can be given as list[float,float,float] to specifier all three dimensions"),
    )


# endclass


# -------------------------------------------------------------------------------------------
@EntryPoint(
    CEntrypointInformation.EEntryType.MODIFIER,
    clsInterfaceDoc=CScaleParams,
)
def Scale(_objX, _dicMod, **kwargs):
    """Scales an object in all three dimensions. Given 3-dim vector,
    or scales the object with one unique value given a float
    """
    paramMod = CScaleParams(_dicMod)

    if _objX.type == "CAMERA":
        objX = camops.GetAnyCamTopObject(_objX.name)
    else:
        objX = _objX
    # endif

    # Set scale of object
    objX.scale = mathutils.Vector(paramMod.lScale)
    anyvl.Update()


# enddef


############################################################################################
############################################################################################
@paramclass
class CDeltaScaleParams:
    sDTI: str = (
        CParamFields.HINT(sHint="entry point identification"),
        CParamFields.REQUIRED("blender/modify/object/delta-scale:1.1"),
        CParamFields.DEPRECATED("sType"),
    )
    lScale: list = (
        CParamFields.REQUIRED(list[float, float, float], float),
        CParamFields.DEPRECATED("xValue"),
        CParamFields.HINT(
            "scale can be given as list[float,float,float] to specifier all three dimensions, or only one float for all dim"
        ),
    )

    def __post_init__(self, _dictArgs):
        # no generic expanding of a single float into a list can be applied
        # check optional types and create the correct value
        if isinstance(self.lScale, float):
            fScale = self.lScale
            self.lScale = [fScale, fScale, fScale]

    # end def


# endclass


# -------------------------------------------------------------------------------------------
@EntryPoint(
    CEntrypointInformation.EEntryType.MODIFIER,
    clsInterfaceDoc=CDeltaScaleParams,
)
def DeltaScale(_objX, _dicMod, **kwargs):
    """Scales an object in each update in all three dimensions. Given 3-dim vector,
    or scales the object with one unique value given a float
    """
    paramMod = CDeltaScaleParams(_dicMod)

    if _objX.type == "CAMERA":
        objX = camops.GetAnyCamTopObject(_objX.name)
    else:
        objX = _objX
    # endif

    # update scale of object
    objX.scale *= mathutils.Vector(paramMod.lScale)
    anyvl.Update()


# enddef


############################################################################################
############################################################################################
@paramclass
class CScaleToSceneParams:
    sDTI: str = (
        CParamFields.HINT(sHint="entry point identification"),
        CParamFields.REQUIRED("blender/modify/object/scale-to-scene:1.1"),
        CParamFields.DEPRECATED("sType"),
    )
    fOrigMeterPerBU: float = (
        CParamFields.DEFAULT(1.0),
        CParamFields.DISPLAY("meter per Blender-Unit"),
        CParamFields.HINT("Blender-Unit is per default unit-free. Determine the phyiscal intention of one BU in meter"),
    )
    lScale: list = (
        CParamFields.REQUIRED(list[float, float, float]),
        CParamFields.DEPRECATED("xValue"),
        CParamFields.HINT("scale can be given as list[float,float,float] to specifier all three dimensions"),
    )


# endclass


# -------------------------------------------------------------------------------------------
@EntryPoint(
    CEntrypointInformation.EEntryType.MODIFIER,
    clsInterfaceDoc=CScaleToSceneParams,
)
def ScaleToSceneUnit(_objX, _dicMod, **kwargs):
    """Scales an object in all three dimensions. Given 3-dim vector,
    or scales the object with one unique value given a float

    The scaling is supposed to be in metern, therefore in advance, fOrigMeterPerBU has to be given
    to scale the objects in physical size manner
    """
    paramMod = CScaleToSceneParams(_dicMod)

    # Unit scale of current scene
    fMeterPerBU = bpy.context.scene.unit_settings.scale_length

    if _objX.type == "CAMERA":
        objX = camops.GetAnyCamTopObject(_objX.name)
    else:
        objX = _objX
    # endif

    # Set scale of object
    if isinstance(paramMod.lScale, list):
        objX.scale = (paramMod.fOrigMeterPerBU / fMeterPerBU) * mathutils.Vector(paramMod.lScale)
    else:
        objX.scale = (
            (paramMod.fOrigMeterPerBU / fMeterPerBU) * float(paramMod.lScale) * mathutils.Vector(1.0, 1.0, 1.0)
        )
    # endif

    anyvl.Update()


# enddef

############################################################################################
############################################################################################
@paramclass
class CPoseInterpolateLinearParams:
    sDTI: str = (
        CParamFields.HINT(sHint="entry point identification"),
        CParamFields.REQUIRED("blender/modify/object/interpolate-pose/linear:1.0"),
    )

    sStartEmpty: str = (
        CParamFields.REQUIRED(str),
        CParamFields.HINT("name of the empty that is used as start point"),
    )

    sEndEmpty: str = (
        CParamFields.REQUIRED(str),
        CParamFields.HINT("name of the empty that is used as end point"),
    )

    fValue: float = (
        CParamFields.REQUIRED(float),
        CParamFields.HINT("relative position/orientation between start and end")
    )

# endclass


# -------------------------------------------------------------------------------------------
@EntryPoint(
    CEntrypointInformation.EEntryType.MODIFIER,
    clsInterfaceDoc=CPoseInterpolateLinearParams,
)
def InterpolatePoseLinear(_objX, _dicMod, **kwargs):
    """
    sets the location of an object
    """

    paramMod = CPoseInterpolateLinearParams(_dicMod)

    objStart = bpy.data.objects.get(paramMod.sStartEmpty)
    if objStart is None:
        raise RuntimeError(f"Start empty object '{paramMod.sStartEmpty}' not found")
    # endif

    objEnd = bpy.data.objects.get(paramMod.sEndEmpty)
    if objEnd is None:
        raise RuntimeError(f"End empty object '{paramMod.sEndEmpty}' not found")
    # endif

    fValue = min(max(paramMod.fValue, 0.0), 1.0)

    vStartPos, qStartRot, vStartScale = objStart.matrix_world.decompose()
    vEndPos, qEndRot, vEndScale = objEnd.matrix_world.decompose()

    vPos = vStartPos.lerp(vEndPos, fValue)
    qRot = qStartRot.slerp(qEndRot, fValue)
    vScale = vStartScale.lerp(vEndScale, fValue)

    # print(f"vStartPos: {vStartPos}, qStartRot: {qStartRot}, vStartScale: {vStartScale}")
    # print(f"vEndPos: {vEndPos}, qEndRot: {qEndRot}, vEndScale: {vEndScale}")
    # print(f"vPos: {vPos}, qRot: {qRot}, vScale: {vScale}")

    matPos = mathutils.Matrix.LocRotScale(vPos, qRot, vScale)

    if _objX.type == "CAMERA":
        objX = camops.GetAnyCamTopObject(_objX.name)
    else:
        objX = _objX
    # endif

    objParent = objX.parent
    if objParent is not None:
        objX.matrix_basis = objParent.matrix_world.inverted() @ matPos
    else:
        objX.matrix_basis = matPos
    # endif

    anyvl.Update()


# enddef



################################################################################
############################################################################################
@paramclass
class CSnapObjToSurfParams:
    sDTI: str = (
        CParamFields.HINT(sHint="entry point identification"),
        CParamFields.REQUIRED("blender/modify/object/snap-to-surf:1.1"),
        CParamFields.DEPRECATED("sType"),
    )

    sTargetObject: str = (
        CParamFields.REQUIRED(str),
        CParamFields.HINT("target object to that objects should be snapped"),
    )
    # to satisfy the json-file (rescue existing configurations) a break in coding name convention,
    # lOffset is more generic than vecOffset or similiar
    lOffset: mathutils.Vector = (
        CParamFields.DEFAULT([0, 0, 0]),
        CParamFields.HINT("Position offset for evaluated positions"),
    )
    lSnapDir: mathutils.Vector = (
        CParamFields.DEFAULT([0, 0, -1]),
        CParamFields.HINT("Snap Direction, default upright for Blender [0,0,-1]"),
    )
    sSnapMode: str = CParamFields.OPTIONS(["ABOVE", "BELOW", "CLOSEST"], xDefault="ABOVE")

    # def __post_init__(self, _dictArgs):
    # will be checked during import-time/default-ctor list[float,float,float]
    # if len(self.lOffset) != 3:
    #     raise CAnyError_Message(
    #         sMsg=f"ParameterField(lOffset) of <{self.sDTI}> is required as list[3]"
    #         f"but was not given by list-length: {len(self.lOffset)}"
    #     )

    # if len(self.lSnapDir) != 3:
    #     raise CAnyError_Message(
    #         sMsg=f"ParameterField(lSnapDir) of <{self.sDTI}> is required as list[3]"
    #         f"but was not given by list-length: {len(self.lSnapDir)}"
    #     )

    # # convert lists to mathutils-vectors
    # # due to ducktyping blender types are also typecasting with convert.ToType() (automatically in default decoratoration and cTor)
    # vecOffset = (self.lOffset)
    # self.lOffset = vecOffset

    # vecSnapDir = mathutils.Vector(self.lSnapDir).normalized()
    # self.lSnapDir = vecSnapDir

    # end def


# endclass


# -------------------------------------------------------------------------------------------
@EntryPoint(CEntrypointInformation.EEntryType.MODIFIER)
def SnapObjToSurf(_objX, _dicMod, **kwargs):
    """Snap object to surface.

    Args:
        _objX (bpy.types.Object): The object that is snapped to the surface.
        _dicMod (dict): A dictionary of placement parameters.

    Configuration Args:
        sTargetObject (str): The name of the target object. The collection objects will be placed on the surface
                        of this object.
        lOffset (list(float), optional): Position offset for evaluated positions.
        lSnapDir (list(float), optional): Snap direction. Default [0,0,-1].
        sSnapMode (string, optional): Snap mode, has to be one of 'ABOVE', 'BELOW', 'CLOSEST'.
    """

    paramMod = CSnapObjToSurfParams(_dicMod)

    objTrg = bpy.data.objects.get(paramMod.sTargetObject)
    if objTrg is None:
        raise RuntimeError("Target surface object '{}' not found".format(paramMod.sTargetObject))
    # endif

    if _objX.type == "CAMERA":
        objX = camops.GetAnyCamTopObject(_objX.name)
    else:
        objX = _objX
    # endif

    vDelta = anyobj.GetObjectDeltaToMesh(objTrg=objTrg, objX=objX, vDir=paramMod.lSnapDir, sMode=paramMod.sSnapMode)
    objX.location += vDelta + paramMod.lOffset
    # Need to call update, so that world matrix of object is also updated
    anyvl.Update()


# enddef


############################################################################################
@paramclass
class CApplyTransformsParams:
    sDTI: str = (
        CParamFields.HINT(sHint="entry point identification"),
        CParamFields.REQUIRED("blender/modify/object/apply-transforms:1.0"),
    )

    bLocation: bool = (
        CParamFields.DEFAULT(True),
        CParamFields.DISPLAY("apply location"),
    )

    bRotation: bool = (
        CParamFields.DEFAULT(True),
        CParamFields.DISPLAY("apply rotation"),
    )

    bScale: bool = (
        CParamFields.DEFAULT(True),
        CParamFields.DISPLAY("apply scale"),
    )

    bProperties: bool = (
        CParamFields.DEFAULT(True),
        CParamFields.DISPLAY("apply properties"),
    )


# endclass


def ApplyTransforms(_objX, _dicMod, **kwargs):
    """
    applies all transformations to the mesh
    """

    paramMod = CApplyTransformsParams(_dicMod)

    anyops.ApplyTransforms(
        _objX,
        _bLocation=paramMod.bLocation,
        _bRotation=paramMod.bRotation,
        _bScale=paramMod.bScale,
        _bProperties=paramMod.bProperties,
    )

    anyvl.Update()


# enddef
