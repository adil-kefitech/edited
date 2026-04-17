#Api for Exam Configuration
from django.shortcuts import render
from util.models import *
from util.serializers import *
from django.http import HttpResponse,Http404 # witten httpresponse
from django.shortcuts import get_object_or_404 # 404 if object is not exists
from rest_framework.views import APIView # normal view can written API data
from rest_framework.response import Response# get a perticular response every thing is okey then give 200 response
from rest_framework import status # basically sent back status
from django.contrib import messages
from django.contrib.auth.models import User
import json
from util.constants import *
from rest_framework import generics
import datetime
from django.utils import timezone
from django.db.models import Q
from rest_framework.exceptions import APIException
from util.pagination import *
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import ListAPIView
from rest_framework import renderers,viewsets
import random
from river.models import State
from river.utils.exceptions import RiverException   
# import logging,traceback
# from logging import *
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
# from django.filters import rest_framework as filters

from rest_framework.exceptions import (
 APIException,               #for api exception
 ValidationError
)
from rest_framework.filters import (
    SearchFilter,
    OrderingFilter
)
from iteration_utilities import unique_everseen #for remove dict
from util.loggings import logging
logger=logging.getLogger(__name__)
from datetime import datetime
import datetime as dt

#================================================================================#
#                      EXAM ADD API START                                        #
#================================================================================#
class ExamConfiguration(ListAPIView):

    def post(self,request):
        try:

            jsondata=request.data
            purpose_list=jsondata.get('purpose_list')
            schedule_list=jsondata.get('schedule_list')
            admission_year_list=jsondata.get('admission_year_list')
            status_fetch=State.objects.filter(label='PENDING').first()
            status_id=status_fetch.id
            user =request.user
            created_by =user             

            prgm_query_set=Programme.objects.filter(id=request.data.get('programme')).first()
            prgm_code=prgm_query_set.code            
            scheme_query_set=SchemeMaster.objects.filter(id=request.data.get('scheme')).first()
            prgm_scheme=scheme_query_set.name            
            prefix=str(prgm_scheme)[-2:]
            semester = ProgrammeSemester.objects.filter(id=request.data.get('programme_semester')).first()
            sem_query_set=SemesterMaster.objects.filter(id=semester.semester.id).first()
            prgm_sem=sem_query_set.title 
            code=prgm_code+prefix+prgm_sem  
            existance_check=Examination.objects.filter(code__icontains=code).order_by('-code').first()
            if existance_check==None:
                code=code+"01"
            else:
                temp=int(existance_check.code[-2:])+1 
                code=code+str(temp).zfill(2)
            exam = ExaminationCreateSerializer(data=request.data,context={'request':request,"code":code,"comments":"Exam created"}) 
            if exam.is_valid(raise_exception=True):
                exam.save()
            # exam_admi_year={"admission_year":request.data.get('admission_year')}
            # exam = ExamAddSerializer(data=request.data) 
            # exam.is_valid(raise_exception=True) 
            # exam_data = exam.save(created_by=created_by,code=code,status=status_fetch,comments="Exam created")
            
            


            # exam_prgm_sem=ExamAddProgrammeSemesterMappingSerializer(data=request.data)
            # exam_prgm_sem.is_valid(raise_exception=True)
            # exam_prgm_sem.save(created_by=created_by,exam=exam_data,status=status_fetch)  
            # for yr in admission_year_list:
            #     admission_year=int(yr)
            #     admi_yr_id=AdmissionYearMaster.objects.get(id=admission_year)  
            #     add_yr=ExaminationAdmissionYear(exam=exam_data,admission_year=admi_yr_id,created_by=created_by,status=status_fetch)  
            #     add_yr.save()    
            # for i in purpose_list:
            #     purpose_id=i.get('purpose_id')
            #     start_date=i.get('start_date')
            #     end_date=i.get('end_date')
            #     purps_id=ExaminationPurposeMaster.objects.get(id=purpose_id)
            #     add_purpose=ExaminationDate(purpose=purps_id,exam=exam_data,start_date=start_date,end_date=end_date,created_by=created_by,status=status_fetch)
            #     add_purpose.save()
            # for i in schedule_list:
            #     programme_semester_course_id=i.get('prgm_course_sem_id')
            #     start_date=i.get('start_date')
            #     end_date=i.get('end_date')
            #     start_time=i.get('start_time')
            #     end_time=i.get('end_time')
            #     exam_type_id=i.get('exam_type_id')
            #     time_display_name=start_time +"-"+ end_time
            #     prgm_sem_course_id=ProgrammeCourseSemester.objects.get(id=programme_semester_course_id)
            #     exam_type=ExaminationTypeMaster.objects.get(id=exam_type_id)
            #     add_schedule=ExaminationSchedule(programme_semester_course=prgm_sem_course_id,exam=exam_data,start_date=start_date,end_date=end_date,time_display_name=time_display_name,created_by=created_by,exam_type=exam_type,start_time=start_time,end_time=end_time,status=status_fetch)
            #     add_schedule.save()

            return format_response(True,EXAM_ADD_SUCCESS_MSG,{},status_code=status.HTTP_201_CREATED,template_name="exam.html") 
            
        except ValidationError as err:
            logger.error(err,exc_info=True)
            er = err.__dict__
            return format_response(False,er,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_400_BAD_REQUEST,template_name="exam.html")
        except Exception as e:
            logger.error(e,exc_info=True)
            return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_400_BAD_REQUEST)

#================================================================================#
#                        EXAM ADD API END                                        #
#================================================================================#

#================================================================================#
#                      GET ALL EXAM API START                                    #
#================================================================================#


    def get(self,request): #getting the data from the table
        
        try:
            program = Programme.objects.all()
            program = ProgrammeMasterSerializers(program,many=True)
            staffbase=StaffBase.objects.filter(user=request.user).first()           
            staffsection=StaffSection.objects.filter(staff=staffbase)
         
            subsection=[]
            for  subsect in staffsection:
                subsection.append(subsect.sub_section)
                
            subsectionprg=SubsectionProgramme.objects.filter(sub_section_id__in=subsection).order_by('-programme__title')
           
            prgm_type=[]
            prgm_grp=[]
            prgm_class=[]
            for subsectprg in subsectionprg:
                if subsectprg.programme.programme_type not in prgm_type:
                    prgm_type.append(subsectprg.programme.programme_type)
                if subsectprg.programme.programme_group not in prgm_grp:
                    prgm_grp.append(subsectprg.programme.programme_group)
                if subsectprg.programme.programme_class not in prgm_class:
                    prgm_class.append(subsectprg.programme.programme_class)

            
            program_typ = ProgrammeTypeMasterSerializers(prgm_type,many=True)
            program_grp = ProgrammeGroupMasterSerializers(prgm_grp,many=True)
            program_cls = ProgrammeClassMasterSerializers(prgm_class,many=True)
            states=[ACTIVE_STATE,PENDING_STATE]

            # exam_obj=Examination.objects.select_related("exam_type","season","question_paper_delivery_type").prefetch_related('admission_yr','prgm_sem','prgm_details','purpose_list','schedule_list').filter(status_id__in=states).all()
            # serialize_data=ExamSerializer(exam_obj,many=True)

            exam_type_obj=ExaminationTypeMaster.objects.all()
            exam_type_data=ExaminationTypeMasterSerializer(exam_type_obj,many=True)
            qp_delivery_obj=ExaminationQuestionPaperDeliveryMaster.objects.all()
            qp_delivery_data=ExamQpDeliverySerializer(qp_delivery_obj,many=True)
            exam_purpose=ExaminationPurposeMaster.objects.all()
            exam_purpose_data=ExaminationPurposeSerializer(exam_purpose,many=True)
            year = timezone.now().year
            date_list=[]
            # date_list.extend([int(year)-1,year,int(year)+1])
            date_list.extend([year])
            # return format_response(True,EXAM_FETCH_SUCCESS_MSG,data={"exam_list":serialize_data.data,"exam_type_list":exam_type_data.data,"qp_delivery_list":qp_delivery_data.data,"exam_purpose_list":exam_purpose_data.data,"prg":program.data,"prg_typ":program_typ.data,"prg_cls":program_cls.data,"prg_grp":program_grp.data,'datelist':date_list},status_code=status.HTTP_200_OK,template_name="exam.html")
            return format_response(True,EXAM_FETCH_SUCCESS_MSG,data={"exam_type_list":exam_type_data.data,"qp_delivery_list":qp_delivery_data.data,"exam_purpose_list":exam_purpose_data.data,"prg":program.data,"prg_typ":program_typ.data,"prg_cls":program_cls.data,"prg_grp":program_grp.data,'datelist':date_list},status_code=status.HTTP_200_OK,template_name="exam.html")

        except Examination.DoesNotExist:
            return format_response(False,PRGM_NOT_FOUND_MSG,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
           logger.error(e,exc_info=True)
           return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)



#================================================================================#
#                      GET ALL EXAM API END                                      #
#================================================================================#

#================================================================================#
#                      SINGLE EXAM GET API START                                 #
#================================================================================#

class ExamSingleGetWithSchedule(ListAPIView):
    def get(self,request,pk):
        try:
            exam_obj=Examination.objects.prefetch_related('admission_yr','prgm_sem','prgm_details','purpose_list','schedule_list').filter(pk=pk).first()
            serialize_data=ExamSerializer(exam_obj)
           
            hist = Examination.history.filter(id=pk).all()
            hist_serializer= ExaminationHistorySerializer(hist,many=True)
            # feecat=FeeCategory.objects.all()
            # feecatse=FeeCategoryserilizer(feecat,many=True),'feecat':feecatse.data
            return format_response(True,EXAM_FETCH_SUCCESS_MSG,data={"exam_details":serialize_data.data,"his_details":hist_serializer.data},status_code=status.HTTP_200_OK,template_name="exam.html")


        except Examination.DoesNotExist:
            return format_response(False,PRGM_NOT_FOUND_MSG,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            logger.error(e,exc_info=True)
            return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_400_BAD_REQUEST)

class ExamSingleGet(ListAPIView):
    def get(self,request,pk):
        try:
            exam_obj=Examination.objects.prefetch_related('admission_yr','prgm_sem','prgm_details','purpose_list').filter(pk=pk).first()
            serialize_data=ExamSingleFtechSerializer(exam_obj)
           
            hist = Examination.history.filter(id=pk).all()
            hist_serializer= ExaminationHistorySerializer(hist,many=True)
            # feecat=FeeCategory.objects.all()
            # feecatse=FeeCategoryserilizer(feecat,many=True),'feecat':feecatse.data
            return format_response(True,EXAM_FETCH_SUCCESS_MSG,data={"exam_details":serialize_data.data,"his_details":hist_serializer.data},status_code=status.HTTP_200_OK,template_name="exam.html")


        except Examination.DoesNotExist:
            return format_response(False,PRGM_NOT_FOUND_MSG,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            logger.error(e,exc_info=True)
            return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_400_BAD_REQUEST)


class ExamWiseSchedule(ListAPIView):
    def get(self,request,pk):
        try:
            exam_obj=Examination.objects.filter(pk=pk).first()
            exm_schld =ExaminationSchedule.objects.filter(exam=exam_obj.id,status__label__in=["ACTIVE","PENDING"])
            exam_name = exam_obj.title
            exam_code = exam_obj.code
            exm_schld_serial=ExamScheduleSerializer(exm_schld,many=True)
            
           
            return format_response(True,EXAM_FETCH_SUCCESS_MSG,data={"exam_details":exm_schld_serial.data,"exam_name":exam_name,"exam_code":exam_code},status_code=status.HTTP_200_OK,template_name="exam.html")


        except Examination.DoesNotExist:
            return format_response(False,PRGM_NOT_FOUND_MSG,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            logger.error(e,exc_info=True)
            return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_400_BAD_REQUEST)

class PrgmSemWiseFeeList(ListAPIView):
    def get(self,request,pk):
        try:
            exam_obj=Examination.objects.prefetch_related('prgm_sem').filter(pk=pk).first()
            serialize_data=ExamFeeFtechSerializer(exam_obj)
            feecat=FeeCategory.objects.all()
            feecatse=FeeCategoryserilizer(feecat,many=True)
           
            return format_response(True,EXAM_FETCH_SUCCESS_MSG,data={'feecat':serialize_data.data,'feetitle':feecatse.data},status_code=status.HTTP_200_OK,template_name="exam.html")


        except Examination.DoesNotExist:
            return format_response(False,PRGM_NOT_FOUND_MSG,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            logger.error(e,exc_info=True)
            return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_400_BAD_REQUEST)
#================================================================================#
#                      SINGLE EXAM GET API END                                   #
#================================================================================#


#================================================================================#
#                      PRGM WISE SEMESTER COURSE LIST API START                  #
#================================================================================#
 
class ProgrammewiseCourseList(ListAPIView):
    permission_classes = (AllowAny,)
    def post(self,request): #getting the data from the table
        try:
            jsondata=request.data
            prgm=jsondata.get('programme_id')
            prgm_sem_map=Programme.objects.get(id=prgm)
            serialize_data=ProgrammeSerializers(prgm_sem_map)
            return format_response(True,COURSE_FETCH_SUCCESS_MSG,data=serialize_data.data,status_code=status.HTTP_200_OK,template_name="exam.html")


        except Programme.DoesNotExist:
            return format_response(False,PRGM_NOT_FOUND_MSG,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
           logger.error(e,exc_info=True)
           return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

#================================================================================#
#                      PRGM WISE SEMESTER COURSE LIST API END                    #
#================================================================================#

#================================================================================#
#                         EXAM APPROVAL API START                                #
#================================================================================#


class ExamApproval(ListAPIView):
    
    def post(self,request):
        approved_by = request.user
        updated_on = timezone.now() 
        try:
            jsondata = request.data
            exam_id=jsondata.get('exam_id')
            text=jsondata.get('comments')
            satus=jsondata.get('next_status')
            status_fetch=State.objects.filter(label=satus).first()
           
            next_status = State.objects.get(label=satus)
            exam=Examination.objects.filter(id=exam_id).first()
            
            prgm_Sem=ExamProgrammeSemesterMapping.objects.filter(exam=exam_id).first()
           
            prgm_Sem_id = prgm_Sem.programme_semester
            
            final_data = ExamProgrammeSemesterMapping.objects.filter(programme_semester=prgm_Sem_id,status_id=ACTIVE_STATE).all()
            
            if final_data.exists():
                 return format_response(False,EXAM_EXIST_APPROVE_MSG,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_200_OK)
               
            else:
                # exam.river.status.approve(as_user=approved_by,next_state=next_status)
                exam.comments=text
                exam.updated_by=approved_by
                exam.updated_on=updated_on
                exam.status=status_fetch
                exam.save()
                
                exam_obj=Examination.objects.filter(id=exam_id).first()
                
                exam_serilizer = ExamApprovalSerializer(exam_obj,context={'approved_by':approved_by,"updated_on":updated_on,"text":text,"next_status":next_status})
                print(exam_serilizer.data)

                #FOR SAVING EXAM CENTER
                
                exm_mp = ExamProgrammeSemesterMapping.objects.filter(exam_id=exam_id).first()
                exam_prgm_data = exm_mp.programme_semester.programme.id
                

                college_prgm = CollegeProgramme.objects.filter(programme=exam_prgm_data).all()
            
                for col in college_prgm:
                    college_id = col.college_department.college
                    college_name = col.college_department.college.name
                    college_code = col.college_department.college.code
                
                    exam_ctr_check = ExaminationCenter.objects.filter(College=college_id).first()
                    if exam_ctr_check:

                        exam_center_exam_map = ExaminationCenterExamMapping(exam_id=exam_id,exam_center=exam_ctr_check,created_by_id=request.user.id,status_id=ACTIVE_STATE)
                        exam_center_exam_map.save()
                    else:
                        exam_center = ExaminationCenter(College=college_id,name=college_name,code=college_code,created_by_id=request.user.id,status_id=ACTIVE_STATE)
                        exam_center.save()

                        exam_center_exam_map = ExaminationCenterExamMapping(exam_id=exam_id,exam_center=exam_center,created_by_id=request.user.id,status_id=ACTIVE_STATE)
                        exam_center_exam_map.save()

                return format_response(True,EXAM_APPROVE_SUCCESS_MSG,{},status_code=status.HTTP_201_CREATED,template_name="exam_list.html")
          
               
        except RiverException as e:
            logger.error(e,exc_info=True)
            
            return format_response(False," ".join(e.args),{},RIVER_ERROR_CODE,status_code=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            logger.error(e,exc_info=True)
            return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)



    
    
#================================================================================#
#                         EXAM APPROVAL API END                                  #
#================================================================================#

#================================================================================#
#                         EXAM DELETE API START                                  #
#================================================================================#

class ExamDelete(ListAPIView):
    
   def post(self,request):
        
        approved_by=request.user
        updated_by = request.user
        updated_on = timezone.now()        
        try:
            jsondata = request.data
            exam_id=jsondata.get('exam_id')
            text=jsondata.get('comments')
            status_fetch=State.objects.filter(label=DELETE_STATE).first()
            
            next_status=State.objects.filter(id=DELETE_STATE).first()
            exam=Examination.objects.filter(id=exam_id).first()
            
            # exam.river.status.approve(as_user=approved_by,next_state=next_status)
            exam.comments=text
            exam.updated_by=approved_by
            exam.updated_on=updated_on
            exam.status=status_fetch
            exam.save()
            exam_obj=Examination.objects.filter(id=exam_id).first()
            
            exam_serilizer = ExamApprovalSerializer(exam_obj,context={'approved_by':approved_by,"updated_on":updated_on,"text":text,"next_status":next_status})
            print(exam_serilizer.data)


            return format_response(True,"Exam deleted successfully",data={},status_code=status.HTTP_200_OK,template_name='exam.html')

        except RiverException as e:
            logger.error(e,exc_info=True)
            error_msg = e.args[0]
            return format_response(False,error_msg,{},VALIDATION_ERROR_CODE,status_code=status.HTTP_400_BAD_REQUEST,template_name='exam.html')
        except Exception as e:
            logger.error(e,exc_info=True)
            return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_400_BAD_REQUEST,template_name='exam.html')

#================================================================================#
#                         EXAM DELETE API END                                    #
#================================================================================#       



# class ExamList(ListAPIView):
#         queryset=Examination.objects.all()
#         serializer_class = ExamSerializer(queryset,many=True)
#         serializer_class = ExamSerializer
        
#         def get(self,*args,**kwargs):
#             queryset=Examination.objects.all()
#             query = self.request.GET.get("q")
#             if query!=None:
#                 queryset_list=queryset.filter(
#                     Q(title__icontains=query)|
#                     Q(exam_type__name__icontains=query)|
#                     Q(code__icontains=query)|
#                     Q(month__icontains=query)|
#                     Q(year__icontains=query)|
#                     Q(admission_year__admission_year__icontains=query)
#                 ).distinct()
#                 serializer_class = ExamSerializer(queryset_list,many=True)
                
#                 return format_response(True,EXAM_FETCH_SUCCESS_MSG,data=serializer_class.data,status_code=status.HTTP_200_OK,template_name="exam.html")
#             else:
#                 serializer_class = ExamSerializer(queryset,many=True)
#                 return format_response(True,EXAM_FETCH_SUCCESS_MSG,data=serializer_class.data,status_code=status.HTTP_200_OK,template_name="exam.html")



# class ExamList(ListAPIView):
#     filter_backends =(DjangoFilterBackend,OrderingFilter)
#     filter_fields = ('title', 'code','month','year','season__title','exam_type__name','question_paper_delivery_type__name','prgm_details__scheme__name')
    
#     def get(self,request):
#         try:  
#             queryset=Examination.objects.select_related('exam_type','question_paper_delivery_type','season').prefetch_related('prgm_details','prgm_details__scheme').all()       
#             query = self.request.GET.get("search")
#             if query!=None:
#                 queryset=queryset.filter(
#                     Q(prgm_sem__semester__title__icontains=query)|
#                     Q(admission_year__admission_year__icontains=query)|
#                     Q(prgm_sem__programme__title__icontains=query)
#                 ).distinct()
                       
#             queryset=self.filter_queryset(queryset)  
#             serializer_class = ExamSerializer(queryset,many=True)            
#             return format_response(True,COURSE_FETCH_SUCCESS_MSG,data=serializer_class.data,status_code=status.HTTP_200_OK,template_name="exam_list.html")

#         except Exception as e:
#             logger.error(e,exc_info=True)
#             return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProgrammeTypeGroup(ListAPIView):
    def get(self,request):
        jsondata = request.GET.get
        prgm_type = jsondata('prg_typ_id')
        prgm_group = jsondata("prg_grp_id")
        prgm_class = jsondata("prg_cls_id")
        if not prgm_class:
            pass
        else:
            staffbase=StaffBase.objects.filter(user=request.user).first()
           
            staffsection=StaffSection.objects.filter(staff=staffbase)
         
            subsection=[]
            for  subsect in staffsection:
                subsection.append(subsect.sub_section)
                
            subsectionprg=SubsectionProgramme.objects.filter(sub_section_id__in=subsection,programme__programme_class=prgm_class,programme__programme_type=prgm_type,programme__programme_group=prgm_group).order_by('-programme__title')
           
            prgm=[]
            for subsectprg in subsectionprg:
                if subsectprg.programme not in prgm:
                    prgm.append(subsectprg.programme)
           
            return format_response(True,{},data={"prg":prgm},status_code=status.HTTP_202_ACCEPTED,template_name='exam_creation_ajax.html')
    
        return format_response(True,{},data={},status_code=status.HTTP_202_ACCEPTED,template_name='exam_creation_ajax.html')



    
    
#================================================================================#
#               PROGRAMME WISE SCHEME SYLLABUS LIST  API   START                #
#================================================================================#

 
class PrgmwiseSchemeSyllabusList(ListAPIView):
    permission_classes = (AllowAny,)
    def post(self,request):
      try:
        prgm_id= request.data['programme_id']
        obj_data = UniversityRegulationSchemeProgramme.objects.filter(programme = prgm_id).all()        
        serialized_data = UniversityRegulationSchemeProgrammeNewSerializer(obj_data,many = True)
        return format_response(True,"success",data={"scheme_list":serialized_data.data},status_code=status.HTTP_201_CREATED,template_name='exam_scheme_ajax.html')
        
      except Exception as e: 
        return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_400_BAD_REQUEST,template_name='exam_scheme_ajax.html')

class PrgmwiseSchemeAdmissionYearList(ListAPIView):
    permission_classes = (AllowAny,)
    def post(self,request):
      try:
        prgm_id= request.data['programme_id']
        scheme_id=request.data['scheme_id']
        obj_data = UniversityRegulationSchemeProgramme.objects.filter(programme = prgm_id,scheme=scheme_id).all()        
        serialized_data = UniversityRegulationSchemeProgrammeSerializer(obj_data,many = True).data
        serialdata = unique_everseen(list(serialized_data))
        return format_response(True,"success",data={"scheme_list":serialdata},status_code=status.HTTP_201_CREATED,template_name='exam_scheme_ajax.html')
        
      except Exception as e: 
        return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_400_BAD_REQUEST,template_name='exam_scheme_ajax.html')


#================================================================================#
#               PROGRAMME WISE SCHEME SYLLABUS LIST  API END                     #
#================================================================================# 

#================================================================================#
#               PROGRAMME AND SCHEME WISE SEMESTER LIST  API START              #
#================================================================================#

 
# class PrgmSchemeWiseSemesterList(ListAPIView):
#     permission_classes = (AllowAny,)
#     def post(self,request):
#         try:

#             prgm_id= request.data['programme_id']
#             scheme_id= request.data['scheme_id']
#             obj_data = UniversityRegulationSchemeProgramme.objects.select_related("scheme","programme","regulation").filter(programme=prgm_id,scheme=scheme_id).first()  
#             serialized_data = PrgmwiseUniversityRegulationSchemeProgrammeSerializer(obj_data)
#             return format_response(True,"success",data={"scheme_list":serialized_data.data},status_code=status.HTTP_201_CREATED,template_name='schemewise_sem_ajax.html')
        
#         except Exception as e:
#             return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_400_BAD_REQUEST,template_name='schemewise_sem_ajax.html')

class PrgmSchemeWiseSemesterList(ListAPIView):
    permission_classes = (AllowAny,)
    def post(self,request):
        try:

            prgm_id= request.data['programme_id']
            scheme_id= request.data['scheme_id']
            prgm_sem = ProgrammeSemester.objects.filter(programme=prgm_id).all().order_by('semester')
            serialized_data = ProgrammeSemesterExamAddSerializer(prgm_sem,many=True)
            return format_response(True,"success",data={"scheme_list":serialized_data.data},status_code=status.HTTP_201_CREATED,template_name='schemewise_sem_ajax.html')
        
        except Exception as e:
            return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_400_BAD_REQUEST,template_name='schemewise_sem_ajax.html')


#================================================================================#
#              PROGRAMME AND SCHEME WISE SEMESTER LIST  API END                  #
#================================================================================# 

#================================================================================#
#               PROGRAMME,SCHEME,SEMESTER WISE COURSE LIST  API START            #
#================================================================================#

 
class SemesterwiseCourseList(ListAPIView):
    permission_classes = (AllowAny,)
    def post(self,request):
        try:

            prgm_id= request.data['programme_id']
            # scheme_id= request.data['scheme_id']
            semester_id = request.data['semester_id']

            prgm_sem = ProgrammeSemester.objects.filter(programme_id=prgm_id,semester_id=semester_id).first()
           
            exam_get = ExamProgrammeSemesterMapping.objects.filter(programme_semester_id=prgm_sem,status_id=ACTIVE_STATE).first()
 
            if exam_get:
                obj_data = ProgrammeSemester.objects.filter(programme = prgm_id,semester=semester_id).all()  
                serialized_data = SemesterwiseCourse(obj_data,many=True)
                
                return format_response(False,EXAM_EXIST_MSG,data={"data_list":serialized_data.data},status_code=status.HTTP_200_OK,template_name='exam.html')
                # return format_response(False,EXAM_EXIST_MSG,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_200_OK,template_name='exam.html')
            else:
                obj_data = ProgrammeSemester.objects.filter(programme = prgm_id,semester=semester_id).all()  
                serialized_data = SemesterwiseCourse(obj_data,many=True)
                
                return format_response(True,"success",data={"data_list":serialized_data.data},status_code=status.HTTP_201_CREATED,template_name='exam.html')
        except Exception as e:
          
            return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_400_BAD_REQUEST,template_name='exam.html')
            
#================================================================================#
#            PROGRAMME,SCHEME,SEMESTER WISE COURSE LIST  API END                 #
#================================================================================# 

#================================================================================#
#                     GET ALL ADMISSION YEAR API START                           #
#================================================================================#

 
class GetAllAdmissionYear(ListAPIView):
    permission_classes = (AllowAny,)
    def get(self,request):
      try:
        
        obj_data = AdmissionYearMaster.objects.filter().all()  
        serialized_data = AdmissionYearSerializer(obj_data,many = True)
        return format_response(True,"success",data={"year_list":serialized_data.data},status_code=status.HTTP_201_CREATED,template_name='get_all_admission_year_ajax.html')
        
      except Exception as e: 
        return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_400_BAD_REQUEST,template_name='get_all_admission_year_ajax.html')


#================================================================================#
#                       GET ALL ADMISSION YEAR API END                           #
#================================================================================# 

#================================================================================#
#                    GET ALL EXAM SEASON API START                               #
#================================================================================#

 
class GetAllExamSeason(ListAPIView):
    permission_classes = (AllowAny,)
    def get(self,request):
      try:
        obj_data = ExaminationSeasonMaster.objects.filter().all()  
        serialized_data = ExaminationSeasonMasterSerializer(obj_data,many = True)
        return format_response(True,"success",data={"season_list":serialized_data.data},status_code=status.HTTP_201_CREATED,template_name='get_all_exam_season_ajax.html')
         
      except Exception as e: 
      
        return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_400_BAD_REQUEST,template_name='get_all_exam_season_ajax.html')


#================================================================================#
#                       GET ALL EXAM SEASON API END                              #
#================================================================================# 

#================================================================================#
#                               EXAM EDIT API START                             #
#================================================================================# 
class ExamEditlist(ListAPIView):
    def get(self,request,pk):
        try:
            programme=Programme.objects.all()
            scheme=SchemeMaster.objects.all()
            semester=SemesterMaster.objects.all()
            examobj=Examination.objects.filter(id=pk)
            serializer_class =ExamEditSerializer(examobj,many=True)            
            exam_type=ExaminationTypeMaster.objects.all()
            exam_t=[]
            for ex in exam_type:
                exam_t.append({'id':ex.id,'name':ex.name})
            quesntype=ExaminationQuestionPaperDeliveryMaster.objects.all()
            quest=[]
            for qs in quesntype:
                quest.append({'id':qs.id,'name':qs.name})
                                
            year = timezone.now().year
            date_list=[]
            date_list.extend([int(year)-1,year,int(year)+1])  

            return format_response(True,"Exam updated successfully",{'exam':serializer_class.data,'exam_type':exam_t,'quest':quest,'programme':programme,'semester':semester,'scheme':scheme,'datelist':date_list},status_code=status.HTTP_202_ACCEPTED,template_name='examedit.html')
           
        except Examination.DoesNotExist:
            return format_response(False,CAMP_SCHEDULE_NOT_FOUND,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(e,exc_info=True)
            return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_400_BAD_REQUEST)

class Examedit(ListAPIView):
    def post(self,request):
        try:
            updated_by = request.user
            updated_on = timezone.now() 
            id=request.data['primary_key']
            purpose_list=request.data['purpose_list']
            schedule_list=request.data['schedule_list']
            exam = Examination.objects.filter(id=id).first()
            exam_ad_yr = ExaminationAdmissionYear.objects.filter(exam=id).first()
            exam_prgm_sem_obj = ExamProgrammeSemesterMapping.objects.filter(exam=id).first()
            exam_serializer = ExamAddSerializer(exam,data=request.data)
            exam_serializer.is_valid(raise_exception=True) 
            exam_data = exam_serializer.save(updated_by=updated_by,updated_on=updated_on,comments="Exam updated")
            # exam_prgm_sem=ExamAddProgrammeSemesterMappingSerializer(exam_prgm_sem_obj,data=request.data)
            # exam_prgm_sem.is_valid(raise_exception=True)
            # exam_prgm_sem.save(updated_by=updated_by,updated_on=updated_on) 
            exam_date=ExaminationDate.objects.filter(exam=id).all()         
            for date in exam_date:
                purpose_id=date.purpose_id
                purpose_id_list=list(filter(lambda x:int(x.get("purpose_id"))==purpose_id,purpose_list))[0]
                s = purpose_id_list.get("start_date")
                date.purpose_id=purpose_id_list.get("purpose_id")
                startdate=datetime.strptime(s, "%Y-%m-%d").date()
                date.start_date=startdate
                e=purpose_id_list.get("end_date")
                enddate=datetime.strptime(e, "%Y-%m-%d").date()
                date.end_date=enddate
                date.updated_by=updated_by
                date.updated_on=updated_on
                date.save()

            exam_schedule=ExaminationSchedule.objects.filter(exam=id).all()
            for schedule in exam_schedule:
                prgm_course_sem_id=schedule.programme_semester_course_id
                schedule_id_list=list(filter(lambda x:int(x.get("prgm_course_sem_id"))==prgm_course_sem_id,schedule_list))[0]
                schedule.prgm_course_sem_id=schedule_id_list.get("prgm_course_sem_id")
                startdate=datetime.fromisoformat(schedule_id_list.get("start_date"))
                schedule.start_date=startdate
                enddate=datetime.fromisoformat(schedule_id_list.get("end_date"))
                schedule.end_date=enddate
                schedule.start_time=schedule_id_list.get('start_time')
                schedule.end_time=schedule_id_list.get('end_time')
                time_display_name=schedule.start_time +"-"+ schedule.end_time
                schedule.exam_type_id=schedule_id_list.get('exam_type_id')
                schedule.updated_by=updated_by
                schedule.updated_on=updated_on
                schedule.save()                        
            return format_response(True,"Exam updated successfully",{},status_code=status.HTTP_202_ACCEPTED,template_name='examedit.html')
            
        except Examination.DoesNotExist:
            return format_response(False,CAMP_SCHEDULE_NOT_FOUND,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(e,exc_info=True)
            return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_400_BAD_REQUEST)




            
#================================================================================#
#                               EXAM EDIT API END                                #
#================================================================================#

# class AllExamGet(ListAPIView):
#     def get(self,request): #getting the data from the table
#         try:
#             program = Programme.objects.all()
#             program = ProgrammeMasterSerializers(program,many=True)
#             program_typ = ProgrammeTypeMaster.objects.all()
#             program_typ = ProgrammeTypeMasterSerializers(program_typ,many=True)
#             program_grp = ProgrammeGroupMaster.objects.all()
#             program_grp = ProgrammeGroupMasterSerializers(program_grp,many=True)
#             program_cls = ProgrammeClassMaster.objects.all()
#             program_cls = ProgrammeClassMasterSerializers(program_cls,many=True)
#             states=[ACTIVE_STATE,PENDING_STATE]
#             exam_obj=Examination.objects.select_related("exam_type","season","question_paper_delivery_type").prefetch_related('admission_yr','prgm_sem','prgm_details','purpose_list','schedule_list').filter(status_id__in=states).all()
#             serialize_data=ExamSerializer(exam_obj,many=True)
#             exam_type_obj=ExaminationTypeMaster.objects.all()
#             exam_type_data=ExaminationTypeMasterSerializer(exam_type_obj,many=True)
#             qp_delivery_obj=ExaminationQuestionPaperDeliveryMaster.objects.all()
#             qp_delivery_data=ExamQpDeliverySerializer(qp_delivery_obj,many=True)
#             exam_purpose=ExaminationPurposeMaster.objects.all()
#             exam_purpose_data=ExaminationPurposeSerializer(exam_purpose,many=True)
            
#             return format_response(True,EXAM_FETCH_SUCCESS_MSG,data={"exam_list":serialize_data.data,"exam_type_list":exam_type_data.data,"qp_delivery_list":qp_delivery_data.data,"exam_purpose_list":exam_purpose_data.data,"prg":program.data,"prg_typ":program_typ.data,"prg_cls":program_cls.data,"prg_grp":program_grp.data},status_code=status.HTTP_200_OK,template_name="exam_list.html")

#         except Examination.DoesNotExist:
#             return format_response(False,PRGM_NOT_FOUND_MSG,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_404_NOT_FOUND)
        
#         except Exception as e:
#            logger.error(e,exc_info=True)
#            return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


#================================================================================#
#                               EXAM RESHEDULE API START                         #
#================================================================================#
class ExamResheduleApi(ListAPIView):
  
              
    def post(self,request):
        try:
            updated_by = request.user
            created_by = request.user
            
            updated_on = timezone.now()
            jsondata = request.data
          
            exam_shedule =jsondata["exam_shedule_id"]
          
            reshedule_start_date =jsondata["reshedule_start_date"]
            reshedule_end_date =jsondata["reshedule_end_date"]
            reshedule_start_time =jsondata["reshedule_start_time"]
            reshedule_end_time =jsondata["reshedule_end_time"]
            time_display_name=reshedule_start_time +"-"+ reshedule_end_time
            # Page.objects.filter(id__in=
            status_fetch=State.objects.filter(label='EXAM RESCHEDULED').first()
            exam_shedule_data = ExaminationSchedule.objects.filter(id__in=exam_shedule)
            
            exam_shedule_list = []
            
            list(map(lambda xy:exam_shedule_list.append(xy),exam_shedule_data))
            
            schedule = [ExaminationSchedule(exam=x.exam,programme_semester_course=x.programme_semester_course,exam_type=x.exam_type,created_by=created_by,start_date=reshedule_start_date,end_date=reshedule_end_date,time_display_name=time_display_name,start_time=reshedule_start_time,end_time=reshedule_end_time,comments="Resheduled",status=status_fetch)for x in exam_shedule_list]
            objs = bulk_create_with_history(schedule, ExaminationSchedule, batch_size=500)
            # list(map(lambda xy:xy.save(),schedule))
            # for i in exam_shedule:
               
            #     exam = i.exam
            #     programme_semester_course=i.programme_semester_course
            #     exam_type = i.exam_type
             
            
               
            #     add_schedule=ExaminationSchedule(programme_semester_course=programme_semester_course,exam=exam,start_date=reshedule_start_date,end_date=reshedule_end_date,time_display_name=time_display_name,created_by=created_by,exam_type=exam_type,start_time=reshedule_start_time,end_time=reshedule_end_time,comments="Resheduled")
            #     add_schedule.save()
               

            return format_response(True,EXAM_RESHL_SUCCESS_MSG,data={},status_code=status.HTTP_201_CREATED,template_name='exam-reschedule.html')
        
        except Exception as e:
            logger.error(e,exc_info=True)
            return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_400_BAD_REQUEST)
    
class ExamSheduleApproval(ListAPIView):
  
   
    def post(self,request):
        try:
            updated_by = request.user
            created_by = request.user
            
            updated_on = timezone.now()
            jsondata = request.data
          
            exam_shedule_id =jsondata["exam_shedule_id"]
            comment =jsondata["comment"]
            satus=jsondata['next_status']
           

            next_status = State.objects.get(label=satus)
            exam_shedule = ExaminationSchedule.objects.filter(id__in=exam_shedule_id)
            
           
            for i in exam_shedule:
                
                serializer_one = ExamRecheduleSerializer(i,data=request.data)
                if serializer_one.is_valid(raise_exception=True):
                    serializer_one.save(comments=comment,updated_by=updated_by,updated_on=updated_on,status=next_status)
               
                # i.river.status.approve(as_user=request.user,next_state=next_status)
               
               

            return format_response(True,EXAM_RESHL_APPROVE_MSG,data={},status_code=status.HTTP_201_CREATED,template_name='exam-reschedule.html')
        
        except Exception as e:
            logger.error(e,exc_info=True)
            return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_400_BAD_REQUEST)

class ExamScheduleSingle(ListAPIView):
    def get(self,request,pk):
        try:
          
            exam_obj=ExaminationSchedule.objects.filter(pk=pk).first()
            serialize_data=ExamScheduleSingleSerializer(exam_obj)
         
            hist = ExaminationSchedule.history.filter(id=pk).all()
           
            hist_serializer= ExamScheduleHistorySerializer(hist,many=True)

            return format_response(True,EXAM_FETCH_SUCCESS_MSG,data={"exam_details":serialize_data.data,"his_details":hist_serializer.data},status_code=status.HTTP_200_OK,template_name="exam.html")

        except Examination.DoesNotExist:
            return format_response(False,PRGM_NOT_FOUND_MSG,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            logger.error(e,exc_info=True)
            return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_400_BAD_REQUEST) 

class ExamScheduleSingleTwo(ListAPIView):
    def get(self,request):
        try:
            jsondata = request.GET.get
            pk_data = jsondata("exam_shedule_id")
           
            exam_obj=ExaminationSchedule.objects.filter(pk=pk_data).first()
            serialize_data=ExamScheduleSingleSerializer(exam_obj)
         
            hist = ExaminationSchedule.history.filter(id=pk_data).all()
           
            hist_serializer= ExamScheduleHistorySerializer(hist,many=True)
          
            return format_response(True,EXAM_FETCH_SUCCESS_MSG,data={"exam_details":serialize_data.data,"his_details":hist_serializer.data},status_code=status.HTTP_200_OK,template_name="exam.html")

        except Examination.DoesNotExist:
            return format_response(False,PRGM_NOT_FOUND_MSG,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            logger.error(e,exc_info=True)
            return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_400_BAD_REQUEST) 

#==================================================================#
#                   EXAM RESHEDULE API END                         #
#==================================================================#




#=================================================================#
#                  EXAM SHEDULE LIST API START                    #
# ================================================================#


class ExamResheduleList(ListAPIView):
    filter_backends =(DjangoFilterBackend,OrderingFilter)
    filter_fields = ()
    

    def get(self,request): #getting the data from the table
        try:
           
            states=[ACTIVE_STATE,CANCEL_STATE,EXAM_RESCHEDULED_STATE]
            staffbase=StaffBase.objects.filter(user=request.user).first()
           
            staffsection=StaffSection.objects.filter(staff=staffbase)

            subsection=[]
            list(map(lambda x:subsection.append(x.sub_section),staffsection))
               
            subsectionprg=SubsectionProgramme.objects.filter(sub_section_id__in=subsection)
           
            prgm=[]
            prgm_type = []
            for subsectprg in subsectionprg:
                if subsectprg.programme not in prgm:
                    prgm.append(subsectprg.programme)
                    prgm_type.append({"typ_id":subsectprg.programme.programme_type.id, "typ_name":subsectprg.programme.programme_type.title})

            prgmtype = list(unique_everseen(prgm_type))
            

            return format_response(True,"success",data={"prg_typ":prgmtype,},status_code=status.HTTP_201_CREATED,template_name='exam-reschedule.html')

        except Examination.DoesNotExist:
            return format_response(False,PRGM_NOT_FOUND_MSG,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_404_NOT_FOUND,template_name='exam-reschedule.html')
        
        except Exception as e:
           logger.error(e,exc_info=True)
           return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,template_name='exam-reschedule.html')

    def post(self,request):
        try: 
            states=[ACTIVE_STATE,CANCEL_STATE,EXAM_RESCHEDULED_STATE]
            search = request.data['search']
            exam_id = search["exam_id"]
            prg_crs = search["course_list"]
            
            queryset=ExaminationSchedule.objects.filter(status_id__in=states, exam_id = exam_id, programme_semester_course = prg_crs).all()

            if queryset.count() > 1:
                if ExaminationSchedule.objects.filter(status_id = EXAM_RESCHEDULED_STATE, exam_id = exam_id, programme_semester_course = prg_crs).exists():
                    queryset = ExaminationSchedule.objects.filter(status_id = EXAM_RESCHEDULED_STATE, exam_id = exam_id, programme_semester_course = prg_crs)
                else:
                    if ExaminationSchedule.objects.filter(status_id__in = [ACTIVE_STATE], exam_id = exam_id, programme_semester_course = prg_crs).exists():
                        queryset = ExaminationSchedule.objects.filter(status_id__in = [ACTIVE_STATE], exam_id = exam_id, programme_semester_course = prg_crs)
                    else:
                        latest_cancel = ExaminationSchedule.objects.filter(status_id__in = [CANCEL_STATE], exam_id = exam_id, programme_semester_course = prg_crs).latest('created_on')

                        queryset = [latest_cancel] if latest_cancel else []
            else:
                queryset = ExaminationSchedule.objects.filter(status_id__in = [CANCEL_STATE, ACTIVE_STATE], exam_id = exam_id, programme_semester_course = prg_crs)
            
          
            serializer_class = RecheduleListViewSerializer(queryset,many=True)   
            
            pupose_list = []
                    
            purpose = ExaminationDate.objects.filter(exam_id = exam_id,purpose_id =EXAM_WITH_SUPR_FINE).first()
            end_date = purpose.end_date
            pupose_list.append(end_date)
            
            return format_response(True,"success",data={"exam_shedule":serializer_class.data,"purpose_end_date":end_date},status_code=status.HTTP_201_CREATED,template_name='exam-reschedule.html')

        except Exception as e:
            logger.error(e,exc_info=True)
            return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class ExamRescheduleSchemeList(ListAPIView):
    def post(self,request):
        try:
            programme = request.data['prgm']
            prg_sem = ProgrammeSemester.objects.filter(programme_id = programme).first()
            prg_crs = ProgrammeCourseSemester.objects.filter(programme_semester=prg_sem).all()
            scheme = []
            for schm in prg_crs:
                scheme.append({"scheme_id":schm.scheme.id, "scheme_name":schm.scheme.title})

            schemes = list(unique_everseen(scheme))

            return format_response(True,"success",data={"scheme":schemes},status_code=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(e,exc_info=True)
            return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ExamRescheduleSemesterList(ListAPIView):
    def post(self,request):
        try:
            programme = request.data['prgm']
            prg_sem = ProgrammeSemester.objects.filter(programme_id = programme).all().order_by("id")
            semester = []
            for sem in prg_sem:
                semester.append({"sem_id":sem.semester.id, "sem_name":sem.semester.title})

            semesters = list(unique_everseen(semester))

            return format_response(True,"success",data={"semester":semesters},status_code=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(e,exc_info=True)
            return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class ExamRescheduleExaminationList(ListAPIView):
    def post(self,request):
        try:
            programme = request.data['prgm']
            sem = request.data['sem']
            scheme = request.data['scheme']

            prg_sem = ProgrammeSemester.objects.filter(programme_id = programme, semester_id = sem).first()
            exm_prg_sem = ExamProgrammeSemesterMapping.objects.filter(programme_semester = prg_sem, scheme_id = scheme).only('id').order_by("-exam_id")

            exam = []
            for exprg in exm_prg_sem:
                exam.append({"exam_id":exprg.exam.id, "exam_code":exprg.exam.code, "exm_year":exprg.exam.year, "exm_month":exprg.exam.month})

            exams = list(unique_everseen(exam))

            return format_response(True,"success",data={"exam":exams},status_code=status.HTTP_200_OK)

        except Exception as e:
            logger.error(e,exc_info=True)
            return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class ExamRescheduleExamCourseList(ListAPIView):
    def post(self,request):
        try:
            exam = request.data['exam']
            exm_crs = ExaminationSchedule.objects.filter(exam_id = exam, status_id__in = [ACTIVE_STATE,CANCEL_STATE,EXAM_RESCHEDULED_STATE]).only('id').order_by("programme_semester_course__course_num")

            courses = []
            for crs in exm_crs:
                courses.append({"exm_crs_id":crs.programme_semester_course.id, "crs_code":crs.programme_semester_course.course.code, "crs_name":crs.programme_semester_course.course.name})

            course = list(unique_everseen(courses))

            return format_response(True,"success",data={"course":course},status_code=status.HTTP_200_OK)

        except Exception as e:
            logger.error(e,exc_info=True)
            return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

#=================================================================#
#                  EXAM SHEDULE LIST API END                      #
# ================================================================#



#=================================================================#
#                  EXAM LIST API START                            #
# ================================================================#

class ExamList(ListAPIView):
    filter_backends =(DjangoFilterBackend,OrderingFilter)
    filter_fields = ('title', 'code','month','year','season__title','exam_type__name','question_paper_delivery_type__name','prgm_details__scheme__name')
    

    def get(self,request): #getting the data from the table
        try:
           
            states=[ACTIVE_STATE,PENDING_STATE]
            staffbase=StaffBase.objects.filter(user=request.user).first()
           
            staffsection=StaffSection.objects.filter(staff=staffbase)
         
            subsection=[]
            for  subsect in staffsection:
                subsection.append(subsect.sub_section)
                
            subsectionprg=SubsectionProgramme.objects.filter(sub_section_id__in=subsection)
           
            prgm=[]
            for subsectprg in subsectionprg:
                if subsectprg.programme not in prgm:
                    prgm.append(subsectprg.programme)
            
            prpg_sem = ProgrammeSemester.objects.filter(programme__in=prgm).all()
            exam_prgm = ExamProgrammeSemesterMapping.objects.filter(programme_semester__in=prpg_sem).all()
            
            exam_list = []
            for exm in exam_prgm:
                exam_list.append(exm.exam.id)
            # print(exam_list)
            exam_obj=Examination.objects.select_related("exam_type","season","question_paper_delivery_type").prefetch_related('admission_yr','prgm_sem','prgm_details','purpose_list','schedule_list').filter(id__in=exam_list,status_id__in=states).all()

            # exam_obj=Examination.objects.select_related("exam_type","season","question_paper_delivery_type").prefetch_related('admission_yr','prgm_sem','prgm_details','purpose_list','schedule_list').filter(status_id__in=states).all()
            serialize_data=ExamListSerializer(exam_obj,many=True)
            exam_data = serialize_data.data

            dup_typ = []
            dup_grp = []
            dup_cls = []
            dup_prgm = []
            dup_schm = []
            dup_sem = []
            dup_status = []
           

            for exam in exam_data:
                dup_status.append({"status":exam["status"]})
              
                for prgm in exam["prgm_details"]:
                    
                    prg_typ = prgm["programme_type"]
                    prg_grp = prgm["programme_group"]
                    prg_cls = prgm["programme_class"]
                    prgmm = prgm["programme"]
                    sem = prgm["semester"]
                    schema = prgm["scheme"]

                    dup_prgm.append({"programme":prgmm})
                    dup_typ.append({"prgtyp":prg_typ})
                    dup_grp.append({"prggrp":prg_grp})
                    dup_cls.append({"prgcls":prg_cls})
                    dup_sem.append({"semester":sem})
                    dup_schm.append({"schema":schema})
           
            programme_type = list(unique_everseen(dup_typ))
            programme_group = list(unique_everseen(dup_grp))
            programme_class = list(unique_everseen(dup_cls))
            programme = list(unique_everseen(dup_prgm))
            semester = list(unique_everseen(dup_sem))
            schema = list(unique_everseen(dup_schm))
            exam_status = list(unique_everseen(dup_status))

           
            return format_response(True,EXAM_FETCH_SUCCESS_MSG,data={"exam_list":serialize_data.data,"prg":programme,"prg_typ":programme_type,"prg_cls":programme_class,"prg_grp":programme_group,"sem":semester,"status":exam_status,"schema":schema},status_code=status.HTTP_200_OK,template_name="exam_list.html")

        except Examination.DoesNotExist:
            return format_response(False,PRGM_NOT_FOUND_MSG,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
           logger.error(e,exc_info=True)
           return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def post(self,request):
        try: 
            states=[ACTIVE_STATE,PENDING_STATE]
            queryset=Examination.objects.select_related("exam_type","season","question_paper_delivery_type").prefetch_related('admission_yr','prgm_sem','prgm_details','purpose_list','schedule_list').filter(status_id__in=states).all()     
            # query = self.request.GET.get("search")
            # srch=request.data.getlist('search')
            srch = request.data.get('search')
            # date_sr = request.data.getlist('date_search')
            date_sr = request.data["date_search"]
            start_data,end_date = date_sr

            # search list order from frontend:
            # [prgm_type, prgm_group, prgm_class, prgm_list, scheme_list, sem_list, status_list]
            search_fields = [
                'prgm_details__programme_semester__programme__programme_type__title__icontains',
                'prgm_details__programme_semester__programme__programme_group__title__icontains',
                'prgm_details__programme_semester__programme__programme_class__title__icontains',
                'prgm_details__programme_semester__programme__title__icontains',
                'prgm_details__scheme__name__icontains',
                'prgm_details__programme_semester__semester__title__icontains',
                'status__label__icontains',
            ]
            search_list = request.data.get('search')
            for idx, query in enumerate(search_list):
                if query and idx < len(search_fields):
                    queryset = queryset.filter(
                        Q(**{search_fields[idx]: query})
                    ).distinct()

            if start_data and end_date :
               
                queryset=queryset.filter(
                         Q(created_on__date__range=(start_data,end_date))
                    ).distinct()

            # queryset=self.filter_queryset(queryset)  

            # sorted in descending(latest-oldest) order
            queryset = self.filter_queryset(queryset).order_by('-id')
            serializer_class = ExamListSerializer(queryset,many=True)   
         

            # states=[ACTIVE_STATE,PENDING_STATE]
            # exam_obj=Examination.objects.select_related("exam_type","season","question_paper_delivery_type").prefetch_related('admission_yr','prgm_sem','prgm_details','purpose_list','schedule_list').filter(status_id__in=states).all()
            # serialize_data=ExamListSerializer(exam_obj,many=True)
            # exam_data = serialize_data.data
            # dup_typ = []
            # dup_grp = []
            # dup_cls = []
            # dup_prgm = []
            # dup_schm = []
            # dup_sem = []
            # dup_status = []
           

            # for exam in exam_data:
            #     dup_status.append({"status":exam["status"]})
            #     for prgm in exam["prgm_details"]:
                    
            #         prg_typ = prgm["programme_type"]
            #         prg_grp = prgm["programme_group"]
            #         prg_cls = prgm["programme_class"]
            #         prgmm = prgm["programme"]
            #         sem = prgm["semester"]
            #         schema = prgm["scheme"]

            #         dup_prgm.append({"programme":prgmm})
            #         dup_typ.append({"prgtyp":prg_typ})
            #         dup_grp.append({"prggrp":prg_grp})
            #         dup_cls.append({"prgcls":prg_cls})
            #         dup_sem.append({"semester":sem})
            #         dup_schm.append({"schema":schema})
           
            # programme_type = list(unique_everseen(dup_typ))
            # programme_group = list(unique_everseen(dup_grp))
            # programme_class = list(unique_everseen(dup_cls))
            # programme = list(unique_everseen(dup_prgm))
            # semester = list(unique_everseen(dup_sem))
            # schema = list(unique_everseen(dup_schm))
            # exam_status = list(unique_everseen(dup_status))

            return format_response(True,EXAM_FETCH_SUCCESS_MSG,data={"exam_list":serializer_class.data},status_code=status.HTTP_200_OK,template_name="exam_list.html")
            # return format_response(True,EXAM_FETCH_SUCCESS_MSG,data={"exam_list":serializer_class.data,"prg":programme,"prg_typ":programme_type,"prg_cls":programme_class,"prg_grp":programme_group,"sem":semester,"status":exam_status,"schema":schema},status_code=status.HTTP_200_OK,template_name="exam_list.html")

        except Exception as e:
            logger.error(e,exc_info=True)
            return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
      



#=================================================================#
#                      EXAM LIST API END                          #
# ================================================================#


#================================================================================#
#               PROGRAMME WISE SCHEME SYLLABUS LIST API START FOR LIST           #
#================================================================================#

 
class PrgmwiseSchemeList(ListAPIView):
    
    def get(self,request):
      try:
        prgm_name= request.GET.get('programme_id')
        scheme_list =[]
        prgm = Programme.objects.filter(title = prgm_name).all()        
        for i in prgm:
          
            prgm_sem = ProgrammeSemester.objects.filter(programme=i).all()
            for j in prgm_sem:
               
                exm_prgm = ExamProgrammeSemesterMapping.objects.filter(semester=j).all()
                for n in exm_prgm:
                    exam_scheme = n.scheme.name
                   
                    scheme_list.append({"exam_scheme":exam_scheme})
            
        scheme = list(unique_everseen(scheme_list))
        return format_response(True,"success",data={"exam_scheme":scheme},status_code=status.HTTP_201_CREATED,template_name='exam_scheme_ajax.html')
        
      except Exception as e: 
        return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_400_BAD_REQUEST,template_name='exam_scheme_ajax.html')


#================================================================================#
#               PROGRAMME WISE SCHEME SYLLABUS LIST  API END  FOR LIST           #
#================================================================================# 

#================================================================================#
#               SCHEME WISE  SEMSTER LIST API START FOR LIST                     #
#================================================================================#

 
class SchemeSemList(ListAPIView):
    
    def get(self,request):
      try:
        scheme_name= request.GET.get('scheme_id')
     
        sem_list =[]
        scheme = SchemeMaster.objects.filter(name = scheme_name).all()   
       
        for i in scheme:
            exm_sem = ExamProgrammeSemesterMapping.objects.filter(scheme=i).all()
           
            for j in exm_sem:
                sem = j.semester.semester.title
              
                sem_list.append({"exam_sem":sem})
                
        sme = list(unique_everseen(sem_list))
        return format_response(True,"success",data={"semester":sme},status_code=status.HTTP_201_CREATED,template_name='exam_scheme_ajax.html')
        
      except Exception as e: 
      
        return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_400_BAD_REQUEST,template_name='exam_scheme_ajax.html')


#================================================================================#
#              SCHEME WISE  SEMSTER LIST  API END  FOR LIST                      #
#================================================================================# 


#================================================================================#
#                       SCHEDULE HISTORY VIEW START                              #
#================================================================================# 
class ScheduleHistoryApi(ListAPIView):
    def post(self,request):
        try:
            states=[CANCEL_STATE]
            exam_id = request.data["exam_id"]
            curs_id = request.data["curs_id"]
            schedule_id = request.data["schedule_id"]
            data_list = []
          

            exam_obj=ExaminationSchedule.objects.filter(id__in=schedule_id).all()
            serialize_schedule=ExamScheduleSingleSerializer(exam_obj,many=True)

            prg_cours = ProgrammeCourseSemester.objects.filter(course__in=curs_id)
          
            for i in prg_cours:
                exam_schedule = ExaminationSchedule.objects.filter(exam__in=exam_id,status_id__in=states,programme_semester_course=i)
                
                if exam_schedule:
                    serializer_data = ExamScheduleDateSerialzer(exam_schedule,many=True)
                    data_list.append({"exam_date":serializer_data.data})

         
           
            hist = ExaminationSchedule.history.filter(id__in=schedule_id).all()
            
            hist_serializer= ExamScheduleHistorySerializer(hist,many=True)

            return format_response(True,"success",data={"date":data_list,"exam":serialize_schedule.data,"history":hist_serializer.data},status_code=status.HTTP_201_CREATED,template_name=None)
            
        except Exception as e: 
           
            
            return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_400_BAD_REQUEST,template_name=None)


#================================================================================#
#                       SCHEDULE HISTORY VIEW END                                #
#================================================================================# 

class Prgmwisefeelist(ListAPIView):
    permission_classes = (AllowAny,)
    def post(self,request):
      try:
        prgm_id= request.data['programme_id']
        sem_id= request.data['semester_id']

        obj_data = ProgrammeSemester.objects.filter(programme = prgm_id,semester=sem_id).all()        
        serialized_data = ProgrammeSemesterExamSerializer(obj_data,many = True)
        feecat=FeeCategory.objects.all()
        feecatse=FeeCategoryserilizer(feecat,many=True)
        return format_response(True,"success",data={"fee_list":serialized_data.data,'feecat':feecatse.data},status_code=status.HTTP_201_CREATED,template_name='exam_scheme_ajax.html')
        
      except Exception as e: 
        return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_400_BAD_REQUEST,template_name='exam_scheme_ajax.html')
    

class Examsingleview(ListAPIView):
    serializer_class=ExamDateSerializer
    serializer_class_exam=ExamSerializer

    def get(self,request):
        exam_id=request.GET.get("exam_id")
        queryset = ExaminationDate.objects.filter(exam_id=exam_id,status__label__in=["ACTIVE","DATE EXTENDED"]).order_by('-purpose_id').reverse()
        data=self.paginate_queryset(queryset)
        serializer=self.serializer_class(data,many=True)
        data=self.get_paginated_response(serializer.data)
        
        return format_response(True,NOT_APP_SUCCESS_MSG,data={'examsingle':serializer.data},status_code=status.HTTP_200_OK, template_name='exam-notification/notification_approval.html')



class ExamMultipleview(ListAPIView):
    serializer_class=ExamDateExtensionSerializer
    def get(self,request):
        checked_data=request.GET.get('status')
        listd=json.loads(checked_data)
        exams=listd.get('id')
        queryset = Examination.objects.filter(id__in=exams).order_by('-id')
        data=self.paginate_queryset(queryset)
        serializer=self.serializer_class(data,many=True)
        data=self.get_paginated_response(serializer.data)        
        purpose=ExaminationPurposeMaster.objects.all().order_by('-id')
        purser=ExaminationPurposeMasterSerializer(purpose,many=True)
        return format_response(True,NOT_APP_SUCCESS_MSG,data={'exammultiple':serializer.data,'purpose':purser.data},status_code=status.HTTP_200_OK,template_name='exam-notification/notification.html')

class ExamExtendList(ListAPIView):
    filter_backends =(DjangoFilterBackend,OrderingFilter)
    filter_fields = ('title', 'code','month','year','season__title','exam_type__name','question_paper_delivery_type__name','prgm_details__scheme__name')
    def get(self,request): #getting the data from the table
        try:
            states=[ACTIVE_STATE,PENDING_STATE,EXAM_DATE_EXTENDED_STATE]
            staffbase=StaffBase.objects.filter(user=request.user).first()           
            staffsection=StaffSection.objects.filter(staff=staffbase)         
            subsection=[]
            list(map(lambda x:subsection.append(x.sub_section),staffsection))                
            subsectionprg=SubsectionProgramme.objects.filter(sub_section_id__in=subsection)
            prgm=[]
            for subsectprg in subsectionprg:
                if subsectprg.programme not in prgm:
                    prgm.append(subsectprg.programme)
            
            prpg_sem = ProgrammeSemester.objects.filter(programme__in=prgm).all()
            exam_prgm = ExamProgrammeSemesterMapping.objects.filter(programme_semester__in=prpg_sem).all()
            exam_id = []
            list(map(lambda x:exam_id.append(x.exam.id),exam_prgm))
            examob=Examination.objects.filter(id__in=exam_id,status_id__in=states).all()
            pending=State.objects.filter(label="PENDING").first()
            active=State.objects.filter(id=ACTIVE_STATE).first()
            date_extend=State.objects.filter(id=EXAM_DATE_EXTENDED_STATE).first()

            exam_objs=Examination.objects.select_related("exam_type","season","question_paper_delivery_type").prefetch_related('admission_yr','prgm_sem','prgm_details','purpose_list','schedule_list').filter(status_id__in=states).all()
            serialized_data=ExamListSerializer(exam_objs,many=True)
            examdateobj=ExaminationDate.objects.all()
            examlist=[]
            for i in examob:
                # transition_approval = i.river.status.recent_approval
                # if(transition_approval!=None):
                    exam_datstat=[]
                    examdate=ExaminationDate.objects.filter(exam_id=i.id).all()
                    for examd in examdate:
                        exam_datstat.append(examd.status)
                    if  date_extend in exam_datstat:
                        stat=date_extend
                    else:
                        stat=active
                    examdic={'id':i.id,'title':i.title,'code':i.code,'status':stat.label}
                    examlist.append(examdic)
            
            exam_data = serialized_data.data
            dup_typ = []
            dup_grp = []
            dup_cls = []
            dup_prgm = []
            dup_schm = []
            dup_sem = []
           
            for exam in exam_data:
                list(map(lambda x:dup_schm.append({"scheme":x["scheme"]}),exam["prgm_details"]))
                list(map(lambda x:dup_sem.append({"semester":x["semester"]}),exam["prgm_details"]))
                list(map(lambda x:dup_prgm.append({"programme":x["programme"]}),exam["prgm_details"]))
                list(map(lambda x:dup_cls.append({"programme_class":x["programme_class"]}),exam["prgm_details"]))
                list(map(lambda x:dup_typ.append({"programme_type":x["programme_type"]}),exam["prgm_details"]))
                list(map(lambda x:dup_grp.append({"programme_group":x["programme_group"]}),exam["prgm_details"]))

            examdatestatuslist=[]
            for date in examdateobj:
                if date.status not in examdatestatuslist:
                    examdatestatuslist.append(date.status)
            
            programme_type = list(unique_everseen(dup_typ))
            programme_group = list(unique_everseen(dup_grp))
            programme_class = list(unique_everseen(dup_cls))
            programme = list(unique_everseen(dup_prgm))
            semester = list(unique_everseen(dup_sem))
            schema = list(unique_everseen(dup_schm))
            return format_response(True,EXAM_FETCH_SUCCESS_MSG,data={"exam_list":examlist,"prg":programme,"prg_typ":programme_type,"prg_cls":programme_class,"prg_grp":programme_group,"sem":semester,"status":examdatestatuslist,"schema":schema},status_code=status.HTTP_200_OK,template_name="exam-date-extention.html")
        except Examination.DoesNotExist:
            return format_response(False,PRGM_NOT_FOUND_MSG,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
           logger.error(e,exc_info=True)
           return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def post(self,request):
        try: 
            states=[ACTIVE_STATE,PENDING_STATE]
            queryset=Examination.objects.select_related("exam_type","season","question_paper_delivery_type").prefetch_related('admission_yr','prgm_sem','prgm_details','purpose_list','schedule_list').filter(status_id__in=states).all()     
            srch=request.data.get('search')
            date_sr = request.data.get('date_search')
            start_data,end_date = date_sr
            pending=State.objects.filter(label="PENDING").first()
            date_extend=State.objects.filter(id=EXAM_DATE_EXTENDED_STATE).first()  
            active=State.objects.filter(id=ACTIVE_STATE).first()

            for n in srch:
              
                query=n
                if query!=None:
                    queryset=queryset.filter(
                        Q(prgm_details__programme_semester__programme__programme_type__title__icontains=query)|
                        Q(prgm_details__programme_semester__programme__programme_group__title__icontains=query)|
                        Q(prgm_details__programme_semester__programme__programme_class__title__icontains=query)|
                        Q(prgm_details__programme_semester__semester__title__icontains=query)|
                        Q(prgm_details__programme_semester__programme__title__icontains=query)|
                        Q(prgm_details__scheme__name__icontains=query)|
                        Q(purpose_list__status__label__icontains=query)

                    ).distinct()

            if start_data and end_date :
               
                queryset=queryset.filter(
                         Q(created_on__date__range=(start_data,end_date))
                    ).distinct()

            queryset=self.filter_queryset(queryset)  
            examlist=[]

            for i in queryset:
                    exam_datstat=[]
                # transition_approval = i.river.status.recent_approval
                # if(transition_approval!=None):
                    examdate=ExaminationDate.objects.filter(exam_id=i.id).all()
                    for examd in examdate:
                        exam_datstat.append(examd.status)
                    if  date_extend in exam_datstat:
                        stat=pending
                    else:
                        stat=active
                    examdic={'id':i.id,'title':i.title,'code':i.code,'status':stat.label}
                    examlist.append(examdic)
            return format_response(True,EXAM_FETCH_SUCCESS_MSG,data={"exam_list":examlist},status_code=status.HTTP_200_OK,template_name="exam-date-extention.html")

        except Exception as e:
            logger.error(e,exc_info=True)
            return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class Examdateexdentupdate(ListAPIView):
    def post(self,request):
        created_by = request.user
        created_on = timezone.now() 
        approved_by=request.user
        try:
            # status_fetch=State.objects.filter(label='PENDING').first()
            created_by = request.user             
            jsondata=request.data
            next_status=State.objects.filter(label="CANCEL").first()
            checked_data=request.POST.get('status')
            check_list=json.loads(checked_data)
            extendlist=jsondata.get('extendlist')
            status_fetch=State.objects.filter(id=EXAM_DATE_EXTENDED_STATE).first()
            # stateid=State.objects.filter(label=EXAM_DATE_EXTENDED_STATE).first()
            
            puplist=json.loads(extendlist)
            puplist.sort(key=lambda x:x.get('purpose'))

            for i in check_list:
                exam_id=Examination.objects.filter(id=i).first()                
                for j in puplist:     

                    
                    purpse_obj=ExaminationPurposeMaster.objects.get(id=j['purpose'])
                    if purpse_obj.name=="Exam Registration":
                        examdateobj=ExaminationDate.objects.filter(exam=exam_id,purpose_id=j['purpose'],status__label="ACTIVE").first()
                        start_date=examdateobj.start_date
                    elif purpse_obj.name=="Exam Registration-with fine":
                        examdateobj=ExaminationDate.objects.filter(exam=exam_id,purpose__code="1",status=status_fetch).last()
                        start_date=examdateobj.end_date+dt.timedelta(days=1)
                    elif purpse_obj.name=="Exam Registration-with super fine":
                        examdateobj=ExaminationDate.objects.filter(exam=exam_id,purpose__code="2",status=status_fetch).last()
                        start_date=examdateobj.end_date+dt.timedelta(days=1)
                    else:
                        examdateobj=ExaminationDate.objects.filter(exam=exam_id,purpose__code="3",status=status_fetch).last()
                        start_date=examdateobj.end_date+dt.timedelta(days=1)
                    ExaminationDate.objects.filter(exam=exam_id,purpose_id=j['purpose'],status__label="ACTIVE").update(status=next_status)
                    # exam_date.river.status.approve(as_user=approved_by,next_state=next_status)
                    enddate=datetime.strptime(j['date'], "%Y-%m-%d").date()
                    add_date=ExaminationDate(exam_id=i,purpose_id=j['purpose'],start_date=start_date,end_date=enddate,created_by=created_by,created_on=created_on,status=status_fetch)
                    add_date.save()            

            return format_response(True,EXAM_FETCH_SUCCESS_MSG,{},status_code=status.HTTP_201_CREATED,template_name="exam.html") 


        except Exception as e:
            logger.error(e,exc_info=True)
            return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ExamExtendApproval(ListAPIView):
    serializer_class=ExamDateExtensionSerializer
    def get(self,request):
        checked_data=request.GET.get('status')
        listd=json.loads(checked_data)
        exams=listd.get('id')
        queryset = Examination.objects.filter(id__in=exams).order_by('-id')
        data=self.paginate_queryset(queryset)
        serializer=self.serializer_class(data,many=True)
        purpose=ExaminationPurposeMaster.objects.all().order_by('-id')
        purser=ExaminationPurposeMasterSerializer(purpose,many=True)
        examdate=HistoricalExaminationDate.objects.filter(exam__in=exams)
        hist_seri=ExamDateHistorySerializer(examdate,many=True)
        return format_response(True,NOT_APP_SUCCESS_MSG,data={'exammultiple':serializer.data,'purpose':purser.data,'history':hist_seri.data},status_code=status.HTTP_200_OK,template_name='exam-notification/notification.html')    
    def post(self,request):
        approved_by = request.user
        updated_on = timezone.now() 
        try:
            status_fetch=State.objects.filter(label='DATE EXTENDED').first()
            next_status=State.objects.filter(label="ACTIVE").first()
            checked_data=request.POST.get('status')
            comment=request.POST.get('comment')
            listd=json.loads(checked_data)
            exams=listd.get('id')
            for i in exams:
                datesobj=ExaminationDate.objects.filter(exam=i,status=status_fetch).all()
                for j in datesobj:
                    # j.river.status.approve(as_user=approved_by,next_state=next_status)
                    j.status=next_status
                    j.comments=comment
                    j.updated_by=approved_by
                    j.updated_on=updated_on
                    # j.save()
                bulk_update_with_history(datesobj, ExaminationDate, ['comments','updated_by','updated_on','status'],batch_size=500)
                            
            return format_response(True,EXAM_APPROVE_SUCCESS_MSG,{},status_code=status.HTTP_201_CREATED,template_name="exam_list.html")
        
        except RiverException as e:
            logger.error(e,exc_info=True)
            
            return format_response(False," ".join(e.args),{},RIVER_ERROR_CODE,status_code=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            logger.error(e,exc_info=True)
            return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ExamExtendRevert(ListAPIView):
    def post(self,request):
        approved_by = request.user
        updated_on = timezone.now() 
        try:
            status_fetch=State.objects.filter(label='PENDING').first()
            next_status=State.objects.filter(label="REVERT").first()
            checked_data=request.POST.get('status')
            comment=request.POST.get('comment')
            listd=json.loads(checked_data)
            exams=listd.get('id')
            for i in exams:
                datesobj=ExaminationDate.objects.filter(exam=i,status=status_fetch).all()
                for j in datesobj:
                    # j.river.status.approve(as_user=approved_by,next_state=next_status)
                    j.status=next_status
                    j.comments=comment
                    j.updated_by=approved_by
                    j.updated_on=updated_on
                    # j.save()
                bulk_update_with_history(datesobj, ExaminationDate, ['comments','updated_by','updated_on','status'],batch_size=500)
            return format_response(True,EXAM_APPROVE_SUCCESS_MSG,{},status_code=status.HTTP_201_CREATED,template_name="exam_list.html")
        
        except RiverException as e:
            logger.error(e,exc_info=True)
            
            return format_response(False," ".join(e.args),{},RIVER_ERROR_CODE,status_code=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            logger.error(e,exc_info=True)
            return format_response(False,BAD_GATEWAY,{},BAD_GATEWAY_ERROR_CODE,status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

