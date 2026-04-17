from re import T
import re
from django.db import close_old_connections
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
# from typing_extensions import Required
from util.models import *
from util.serializers import *

from django.http import HttpResponse,Http404 # witten httpresponse
from django.shortcuts import get_object_or_404 # 404 if object is not exists
from rest_framework.views import APIView # normal view can written API data
from rest_framework.response import Response# get a perticular response every thing is okey then give 200 response
from rest_framework import status # basically sent back status
from django.contrib import messages
from django.contrib.auth.models import User,Group
import json
from util.constants import *
from util.urls import *
import logging,traceback
from rest_framework import generics
import datetime
from django.utils import timezone
from django.db.models import Q
from rest_framework.exceptions import APIException
from django.contrib.auth import authenticate,login as lg, logout
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.authtoken.models import Token
import random
from rest_framework import permissions
from rest_framework.generics import ListAPIView
from django.contrib import messages # message
#email
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMessage 
from django.conf import settings 
from django.core.mail import send_mail 
from django.core import mail 
from django.template.loader import render_to_string 
from django.utils.html import strip_tags 
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from simple_history.utils import bulk_create_with_history,bulk_update_with_history

import base64
#================mfa===============#
from mfa.models import User_Keys

logger = logging.getLogger(__name__)


class ExtDistrictList(APIView):
    def get(self, request):
        try:
            user = request.user

            distobj = District.objects.filter(id__in=[1, 2, 3, 4]).all()
            distlist = []
            for dist in distobj:
                district = dist.title
                distlist.append(district)

            semobj = SemesterMaster.objects.all()
            semlist = []
            for sem in semobj:
                semid = sem.id
                semlist.append(semid)  # Append semid instead of an empty value

            batchobj = AdmissionYearMaster.objects.all()
            batchlist = []
            for batch in batchobj:
                batchid = batch.admission_year
                batchlist.append(batchid)

            return format_response(
                True,
                PROGRAMME_CATEGORY_FETCH_SUCCESS_MSG,
                data={
                    "district": distlist,
                    "semlist": semlist,
                    "batchlist": batchlist
                },
                status_code=status.HTTP_200_OK,
                template_name="exttchallocation.html",
            )

        except Exception as e:
            print(e)
            logger.error(e, exc_info=True)
            return format_response(
                False,
                BAD_GATEWAY,
                {},
                BAD_GATEWAY_ERROR_CODE,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
    
    def post(self,request):
        try:
            
            jsondata = request.data
            
            dist = jsondata["dist_type"]
            print("///////",dist)
            
            distobj=District.objects.filter(title=dist).first()
            print("///////",distobj)
            distid=distobj.id
            print("///////",distid)
            collobj=AffiliatedCollege.objects.filter(district_id=distid).all()
            print("///////",collobj)
            colleges = AffiliatedCollegeSerializer(collobj, many=True).data
            print("///////",colleges)
            return format_response(True,PROGRAMME_CATEGORY_FETCH_SUCCESS_MSG,data={"collglist":colleges},status_code=status.HTTP_201_CREATED,template_name='exttchallocation.html')

        except  Exception as e:
            
            logger.error(e,exc_info=True)
            return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_400_BAD_REQUEST,template_name='exttchallocation.html')

class ExtProgrammeList(APIView):
   
    def post(self, request):
        try:
            user = request.user
            collobj = request.data['college']
            print("////////", collobj)
            extobj=ExtTeacherAllocation.objects.filter(college_id=collobj,status_id=81).all()
            users=[]
            for ext in extobj:

                userobj=ext.user_id
                users.append(userobj)
            usernameobj = User.objects.filter(id__in=users).all()
                
                
            userobj=UserSerializer(usernameobj, many=True).data
            dept_id = CollegeDepartment.objects.filter(college_id=collobj).all()
            
            prglist = []  # Initialize prglist here
            
            for dept in dept_id:
                coldept_id = dept.id
                colprgobj = CollegeProgramme.objects.filter(college_department_id=coldept_id).all()

                for prg in colprgobj:
                    prg_id = prg.programme_id
                    prgname=Programme.objects.filter(id=prg_id).first().name
                    prglist.append(prg_id)
                    prglist.append(prgname)
            return format_response(True,PROGRAMME_CATEGORY_FETCH_SUCCESS_MSG,data={"prglist":prglist,"userobj":userobj},status_code=status.HTTP_201_CREATED,template_name='exttchallocation.html')
           
        except Exception as e:
            print(e)
            logger.error(e, exc_info=True)
            return Response({
                'success': False,
                'message': str(e),
            }, status=status.HTTP_400_BAD_REQUEST)
class ExternalSchemes(APIView):
    def post(self,request):
        try:
            pgm_id=request.data.get('programme_id')
            scheme_obj=UniversityRegulationSchemeProgramme.objects.filter(programme_id=pgm_id).all()
            schemes=UniversityRegulationSchemeProgrammeNewSerializer(scheme_obj,many=True).data
            programme_semester_obj=ProgrammeSemester.objects.filter(programme_id=pgm_id).all()
            semesters=ProgrammeSemesterSerializer(programme_semester_obj,many=True).data
            data={
                "schemes":schemes,
                "semesters":semesters
            }
            return format_response(
            True,
            FETCH_SUCCESS_MSG,
            data =data,
            status_code=status.HTTP_200_OK,
            template_name='exttchallocation.html'
        )
        except Exception as e:
            logger.error(e,exc_info=True)
            return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,template_name='scrutiny_application_list_camp_wise.html')
class TeacherFetch(APIView):
    def post(self, request):
        try:
            jsondata = request.data
            search_id = jsondata["search_id"]
            print("////////",search_id)

            userobj = None

            if "@" in search_id:  # Check if it's an email
                userobj = User.objects.filter(email=str(search_id)).first()
                
            else:  # Check if it's a beneficiary ID (contains only digits)
                
                usernameobj = TeacherBase.objects.filter(beneficiary_id=str(search_id)).first()
                userobj = User.objects.filter(id=usernameobj.user_id).first()
                
            if userobj:
                usernameobj = User.objects.filter(id=userobj.id).first()
                
                teachusr=usernameobj.id
                
                roleobj=userobj.groups.all()
                role=[]
                for desig in roleobj:
                    desigobj=Group.objects.filter(id=desig.id).first()
                    designme=desigobj.name
                    role.append(designme)
                teachobj=TeacherBase.objects.filter(user_id=userobj.id).first()
                
                collteachobj=CollegeTeacher.objects.filter(teacher_id=teachobj.id).first().college_id
                
                collobjects=AffiliatedCollege.objects.filter(id=collteachobj).first()
                collobj=collobjects.name
                

                mob_no = UserProfiles.objects.filter(user_id=userobj.id).first()
                mail_id = usernameobj.email
                mobile = mob_no.mobile_number
                username=usernameobj.username
                first_name = usernameobj.first_name
                last_name = usernameobj.last_name
                fullname = f"{first_name} {last_name}"
                return format_response(True,REMOVE_SUCCESS_MESSAGE,data={"fullname": fullname,"mail_id": mail_id,"collobj":collobj,"username":username},status_code=status.HTTP_201_CREATED,template_name='exttchallocation.html')

               
            else:
                return Response({"message": "User not found"}, status=status.HTTP_NOT_FOUND)

        except Exception as e:
            return Response(
                {"message": "An error occurred"},
                status=status.HTTP_400_BAD_REQUEST
            )
class ExtcoursesList(APIView):
   
       
    def post(self, request):
        try:

            semobj=request.data['sem_id']
            prgobj=request.data['programme_id']
            prg_sem_id=ProgrammeSemester.objects.filter(programme_id=prgobj,semester_id=semobj).first().id
            prgcourse = ProgrammeCourseSemester.objects.filter(
                programme_semester=prg_sem_id
            ).all()
            prgcors=[]
            for cour in prgcourse:
                prgcorsid=cour.id
                prgcors.append(prgcorsid)
           
            prgcorsobj=Commissioncors.objects.filter(prgm_cors_sem_id_id__in=prgcors).all()
            prgcorsid=[]

            for y in prgcorsobj:
                z=y.prgm_cors_sem_id_id
                prgcorsid.append(z)
            course = ProgrammeCourseSemester.objects.filter(
                id__in=prgcorsid
            ).all()
            cors_dta = []
            srzlr_data = []
            for x in course:
                cors_dta.append(x.course.name)
                # if cors_dta.count(x.course.name) == 1: #commented b'coz dont know the purpose of this line of code .
                srzlr_data.append(TeacherProgramCourseListSerializers(x).data)
            print("///////",srzlr_data)
            return format_response(
                True,
                PROGRAMME_CATEGORY_FETCH_SUCCESS_MSG,
                data={
                        "course": srzlr_data,
                        "prg_sem_id":prg_sem_id 
                    },
                status_code=status.HTTP_200_OK,
                template_name="exttchallocation.html",
            )
           
        except Exception as e:
            print(e)
            logger.error(e, exc_info=True)
            return format_response(
                False,
                BAD_GATEWAY,
                {},
                BAD_GATEWAY_ERROR_CODE,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

class ExtProgramAllocation(APIView):
   
       
    def post(self, request):
        try:

            user = request.user
            userid=user.id
            created_on=timezone.now()
            collobj=request.data['coll_id']
            semobj=request.data['sem_id']

            prgobj=request.data['prg_id']

            corsobj=request.data['cors_id']

            admid=request.data['admid']
            zoneid=request.data['zoneid']

           
            search_id = request.data["search_id"]
            tchruserobj = None

            if "@" in search_id:  # Check if it's an email
                tchruserobj = User.objects.filter(email=str(search_id)).first()
                
            else:  # Check if it's a beneficiary ID (contains only digits)
                
                usernameobj = TeacherBase.objects.filter(beneficiary_id=str(search_id)).first()
                tchruserobj = User.objects.filter(id=usernameobj.user_id).first()
                
            if tchruserobj:
                usernameobj = User.objects.filter(id=tchruserobj.id).first()
                
                teachusr=usernameobj.id
            
            admobj=AdmissionYearMaster.objects.filter(admission_year=admid).first()
            batchid=Batch.objects.filter(academic_year_id=admobj.id).first().id
            print("22222222",batchid)

            userobj=User.objects.filter(id=user.id).first()
            # userobj.groups.add()
            colprgobj=CollegeProgramme.objects.filter(programme_id=prgobj).all()
            print("22222222",colprgobj)

            deptid=[]
            for colprg in colprgobj:
                colldeptid=colprg.college_department_id
                    
                dept_id=CollegeDepartment.objects.filter(id=colldeptid,college_id= collobj).first()
                if dept_id:

                    deptid.append(dept_id.id)
              
            colprgid=CollegeProgramme.objects.filter(college_department_id__in=deptid,programme_id=prgobj).first()
            print("22222222",colprgid)

            prg_sem_id=ProgrammeSemester.objects.filter(programme_id=prgobj,semester_id=semobj).first()
            print("22222222",prg_sem_id)

            colbatchid=CollegeBatchProgramme.objects.filter(college_programm_id=colprgid.id,batch_id=batchid).first()
            print("3333333",colbatchid)

            colbatchsemid=CollegeBatchProgrammeSemester.objects.filter(college_batch_prgm_id=colbatchid.id,prgm_semester_id=prg_sem_id.id).first().id
            print("3333333",colbatchsemid)

            prg_cors_obj=ProgrammeCourseSemester.objects.filter(programme_semester_id=prg_sem_id,course_id=corsobj).first()
            print("3333333",prg_cors_obj)

            exttchobj=ExtTeacherAllocation.objects.filter(prgm_cors_sem_id=prg_cors_obj.id,collegebatch_prgm_sem_id=colbatchsemid,user_id=teachusr).first()
            print("3333333",exttchobj)

            if exttchobj==None:
              
                userobj.groups.add(52)
                print("?//////")

                extteachallocationobj=ExtTeacherAllocation(created_on=created_on,created_by_id=userid,prgm_cors_sem_id=prg_cors_obj.id,collegebatch_prgm_sem_id=colbatchsemid,user_id=teachusr,status_id=ACTIVE_STATE,parent_id=zoneid)
                extteachallocationobj.save()
                return format_response(True, EXT_SUCCSS_MSG, status_code=status.HTTP_200_OK, template_name='exttchallocation.html')

           
        except Exception as e:
            print(e)
            logger.error(e, exc_info=True)
            return format_response(
                False,
                BAD_GATEWAY,
                {},
                BAD_GATEWAY_ERROR_CODE,
                status_code=status.HTTP_400_BAD_REQUEST,
            )